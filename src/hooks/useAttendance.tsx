import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react';
import type { ActiveSession, AttendanceRecord, BluetoothVerificationContext, ScanResult } from '@/types';
import { isSupabaseConfigured } from '@/lib/supabase/client';
import {
  createAttendanceSession,
  endAttendanceSession,
  getStudentDetails,
  isStudentEnrolledInCourse,
  loadAttendanceSnapshot,
  recordAttendanceScan,
  subscribeToAttendanceChanges,
} from '@/services/universityService';
import { useAuth } from '@/hooks/useAuthHooks';

const ACTIVE_SESSIONS_STORAGE_KEY = 'attendance-management-active-sessions';
const ATTENDANCE_RECORDS_STORAGE_KEY = 'attendance-management-attendance-records';

function readStoredState<T>(key: string): T | null {
  if (typeof window === 'undefined') return null;

  try {
    const stored = window.localStorage.getItem(key);
    if (!stored) return null;

    return JSON.parse(stored) as T;
  } catch {
    return null;
  }
}

function normalizeActiveSessions(sessions: ActiveSession[]): ActiveSession[] {
  const now = new Date();

  return sessions.map(session => {
    if (session.isActive && new Date(session.expiresAt) < now) {
      return { ...session, isActive: false };
    }

    return session;
  });
}

interface AttendanceContextType {
  activeSessions: ActiveSession[];
  attendanceRecords: AttendanceRecord[];
  generateSession: (
    courseId: string,
    courseCode: string,
    courseTitle: string,
    lecturerId: string,
    lecturerName: string,
    room: string,
    totalStudents: number,
    duration: number,
    options?: {
      requiresBluetooth?: boolean;
      bluetoothDeviceName?: string;
      bluetoothServiceUuid?: string;
    }
  ) => ActiveSession;
  endSession: (sessionId: string) => void;
  scanBarcode: (
    barcodeData: string,
    studentId: string,
    bluetoothContext?: BluetoothVerificationContext
  ) => Promise<ScanResult>;
  getStudentAttendance: (studentId: string) => AttendanceRecord[];
  getCourseAttendance: (courseId: string) => AttendanceRecord[];
  getActiveSessionForCourse: (courseId: string) => ActiveSession | undefined;
}

const AttendanceContext = createContext<AttendanceContextType | undefined>(undefined);

export function AttendanceProvider({ children }: { children: ReactNode }) {
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>(() => {
    const storedSessions = readStoredState<ActiveSession[]>(ACTIVE_SESSIONS_STORAGE_KEY);
    return normalizeActiveSessions(storedSessions ?? []);
  });
  const [attendanceRecords, setAttendanceRecords] = useState<AttendanceRecord[]>(() => {
    return readStoredState<AttendanceRecord[]>(ATTENDANCE_RECORDS_STORAGE_KEY) ?? [];
  });

  useEffect(() => {
    if (typeof window === 'undefined' || isSupabaseConfigured) return;

    window.localStorage.setItem(ACTIVE_SESSIONS_STORAGE_KEY, JSON.stringify(normalizeActiveSessions(activeSessions)));
    window.localStorage.setItem(ATTENDANCE_RECORDS_STORAGE_KEY, JSON.stringify(attendanceRecords));
  }, [activeSessions, attendanceRecords]);

  const { user } = useAuth();

  useEffect(() => {
    if (!isSupabaseConfigured || !user) return;

    let isMounted = true;

    loadAttendanceSnapshot().then(({ activeSessions: remoteSessions, attendanceRecords: remoteRecords }) => {
      if (!isMounted) return;

      setActiveSessions(normalizeActiveSessions(remoteSessions));
      setAttendanceRecords(remoteRecords);
    });

    const cleanup = subscribeToAttendanceChanges(
      (session) => {
        setActiveSessions(prev => {
          const existingIndex = prev.findIndex(item => item.id === session.id);
          if (existingIndex === -1) return [...prev, session];

          const next = [...prev];
          next[existingIndex] = session;
          return next;
        });
      },
      (record) => {
        setAttendanceRecords(prev => {
          const existingIndex = prev.findIndex(item => item.id === record.id);
          if (existingIndex === -1) return [record, ...prev];

          const next = [...prev];
          next[existingIndex] = record;
          return next;
        });
      }
    );

    return () => {
      isMounted = false;
      cleanup?.();
    };
  }, [user]);

  const generateSession = useCallback((
    courseId: string,
    courseCode: string,
    courseTitle: string,
    lecturerId: string,
    lecturerName: string,
    room: string,
    totalStudents: number,
    duration: number = 15,
    options?: {
      requiresBluetooth?: boolean;
      bluetoothDeviceName?: string;
      bluetoothServiceUuid?: string;
    }
  ): ActiveSession => {
    const now = new Date();
    const expiresAt = new Date(now.getTime() + duration * 60000);
    
    // Generate unique barcode data
    const barcodeData = `${courseCode}-${now.toISOString().split('T')[0]}-${now.getHours()}${now.getMinutes()}-${lecturerId}-${Math.random().toString(36).substring(2, 8)}`;
    
    const newSession: ActiveSession = {
      id: crypto.randomUUID(),
      courseId,
      courseCode,
      courseTitle,
      lecturerId,
      lecturerName,
      barcodeData,
      createdAt: now.toISOString(),
      expiresAt: expiresAt.toISOString(),
      duration,
      scannedStudents: [],
      totalStudents,
      room,
      isActive: true,
      requiresBluetooth: options?.requiresBluetooth ?? false,
      bluetoothDeviceName: options?.bluetoothDeviceName,
      bluetoothServiceUuid: options?.bluetoothServiceUuid
    };
    
    setActiveSessions(prev => [...prev, newSession]);

    void createAttendanceSession(newSession).then(remoteSession => {
      setActiveSessions(prev => prev.map(session => session.id === remoteSession.id ? remoteSession : session));
    });

    return newSession;
  }, []);

  const endSession = useCallback((sessionId: string) => {
    setActiveSessions(prev => 
      prev.map(session => 
        session.id === sessionId 
          ? { ...session, isActive: false }
          : session
      )
    );

    void endAttendanceSession(sessionId);
  }, []);

  const scanBarcode = useCallback(async (
    barcodeData: string,
    studentId: string,
    bluetoothContext?: BluetoothVerificationContext
  ): Promise<ScanResult> => {
    const rawBarcode = barcodeData.trim();
    let session = activeSessions.find(s => s.barcodeData.trim() === rawBarcode);
    
    if (!session) {
      if (isSupabaseConfigured && supabase) {
        const { data, error } = await supabase
          .from('attendance_sessions')
          .select('*')
          .eq('barcode_data', rawBarcode)
          .single();
          
        if (!error && data) {
          // @ts-expect-error - we know mapSessionRow works but it's in a different file, we can reconstruct or fetch via service
          session = {
            id: data.id,
            courseId: data.course_id,
            courseCode: data.course_code,
            courseTitle: data.course_title,
            lecturerId: data.lecturer_id,
            lecturerName: data.lecturer_name,
            barcodeData: data.barcode_data,
            createdAt: data.created_at,
            expiresAt: data.expires_at,
            duration: data.duration_minutes,
            scannedStudents: data.scanned_student_ids ?? [],
            totalStudents: data.total_students,
            room: data.room,
            isActive: data.is_active,
            requiresBluetooth: data.requires_bluetooth,
            bluetoothDeviceName: data.bluetooth_device_name ?? undefined,
            bluetoothServiceUuid: data.bluetooth_service_uuid ?? undefined,
          };
          
          setActiveSessions(prev => {
            if (!session) return prev;
            const exists = prev.find(s => s.id === session!.id);
            if (!exists) return [...prev, session];
            return prev.map(s => s.id === session!.id ? session! : s);
          });
        }
      }
    }

    if (!session) {
      return {
        success: false,
        message: 'Invalid QR code. This code does not match any known session.'
      };
    }

    if (!session.isActive) {
      return {
        success: false,
        message: 'This attendance session has been closed by the lecturer.'
      };
    }
    
    // Check if session has expired
    const now = new Date();
    const expiresAt = new Date(session.expiresAt);
    if (now > expiresAt) {
      return {
        success: false,
        message: 'This attendance session has expired based on the time limit.'
      };
    }
    
    // Check if student already scanned
    if (session.scannedStudents.includes(studentId)) {
      return {
        success: false,
        message: 'You have already marked attendance for this session.'
      };
    }
    
    // Check if student is enrolled in the course
    const isEnrolled = await isStudentEnrolledInCourse(studentId, session.courseId);
    
    if (!isEnrolled) {
      return {
        success: false,
        message: 'You are not enrolled in this course.'
      };
    }

    if (session.requiresBluetooth) {
      if (!bluetoothContext?.bluetoothVerified) {
        return {
          success: false,
          message: 'Bluetooth verification is required before attendance can be recorded.'
        };
      }

      if (
        session.bluetoothDeviceName &&
        bluetoothContext.bluetoothDeviceName &&
        !bluetoothContext.bluetoothDeviceName.toLowerCase().includes(session.bluetoothDeviceName.toLowerCase())
      ) {
        return {
          success: false,
          message: 'Connected Bluetooth device does not match this session.'
        };
      }
    }
    
    const student = await getStudentDetails(studentId);

    const attendanceRecord = await recordAttendanceScan({
      session,
      studentId,
      studentName: student?.name || 'Unknown',
      studentMatric: student?.matricNumber || 'Unknown',
      bluetoothDeviceName: bluetoothContext?.bluetoothDeviceName,
      bluetoothDeviceId: bluetoothContext?.bluetoothDeviceId,
    });

    if (!attendanceRecord) {
      return {
        success: false,
        message: 'Unable to save attendance to the database. Please try again.'
      };
    }
    
    // Add student to scanned list
    setActiveSessions(prev => 
      prev.map(s => 
        s.id === session.id 
          ? { ...s, scannedStudents: [...s.scannedStudents, studentId] }
          : s
      )
    );
    
    // Create attendance record
    setAttendanceRecords(prev => [...prev, attendanceRecord]);
    
    return {
      success: true,
      message: `Attendance marked successfully for ${session.courseCode}: ${session.courseTitle}`,
      courseName: session.courseTitle,
      timestamp: now.toLocaleTimeString()
    };
  }, [activeSessions]);

  const getStudentAttendance = useCallback((studentId: string): AttendanceRecord[] => {
    return attendanceRecords.filter(r => r.studentId === studentId);
  }, [attendanceRecords]);

  const getCourseAttendance = useCallback((courseId: string): AttendanceRecord[] => {
    return attendanceRecords.filter(r => r.courseId === courseId);
  }, [attendanceRecords]);

  const getActiveSessionForCourse = useCallback((courseId: string): ActiveSession | undefined => {
    return activeSessions.find(s => s.courseId === courseId && s.isActive);
  }, [activeSessions]);

  return (
    <AttendanceContext.Provider value={{
      activeSessions,
      attendanceRecords,
      generateSession,
      endSession,
      scanBarcode,
      getStudentAttendance,
      getCourseAttendance,
      getActiveSessionForCourse
    }}>
      {children}
    </AttendanceContext.Provider>
  );
}

export function useAttendance() {
  const context = useContext(AttendanceContext);
  if (context === undefined) {
    throw new Error('useAttendance must be used within an AttendanceProvider');
  }
  return context;
}
