import { createClient } from '@supabase/supabase-js';
import * as dotenv from 'dotenv';
import { resolve } from 'path';

dotenv.config({ path: resolve(process.cwd(), '.env') });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase credentials in .env');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function setup() {
  console.log('Starting test data setup...');

  try {
    // 1. Create Admin
    console.log('Creating Admin...');
    const { data: adminData, error: adminErr } = await supabase.auth.signUp({
      email: process.env.VITE_TEST_ADMIN_EMAIL!,
      password: process.env.VITE_TEST_ADMIN_PASSWORD!,
      options: {
        data: {
          role: 'admin',
          full_name: 'System Admin',
          staff_id: 'ADM/001'
        }
      }
    });
    if (adminErr) throw adminErr;
    console.log('Admin created:', adminData.user?.email);

    // 2. Create Lecturer
    console.log('Creating Lecturer...');
    const { data: lecturerData, error: lecturerErr } = await supabase.auth.signUp({
      email: process.env.VITE_TEST_LECTURER_EMAIL!,
      password: process.env.VITE_TEST_LECTURER_PASSWORD!,
      options: {
        data: {
          role: 'lecturer',
          full_name: process.env.VITE_TEST_LECTURER_NAME!,
          staff_id: 'LEC/001',
          position: 'Senior Lecturer'
        }
      }
    });
    if (lecturerErr) throw lecturerErr;
    console.log('Lecturer created:', lecturerData.user?.email);

    // 3. Create Student
    console.log('Creating Student...');
    const { data: studentData, error: studentErr } = await supabase.auth.signUp({
      email: process.env.VITE_TEST_STUDENT_EMAIL!,
      password: process.env.VITE_TEST_STUDENT_PASSWORD!,
      options: {
        data: {
          role: 'student',
          full_name: 'Test Student',
          matric_number: process.env.VITE_TEST_STUDENT_MATRIC!,
          level: 400
        }
      }
    });
    if (studentErr) throw studentErr;
    console.log('Student created:', studentData.user?.email);

    // Wait a moment for triggers to run and profile rows to be created
    await new Promise(r => setTimeout(r, 2000));

    // 4. Create Courses
    console.log('Creating Test Courses...');
    const courseCodes = [
      process.env.VITE_TEST_COURSE_CODE!,
      'CSC 401', 'IFT 422', 'CSC 452', 'CSC 402', 'CSC 408'
    ];
    
    for (const code of courseCodes) {
      const { error: courseErr } = await supabase.from('courses').insert({
        code: code,
        title: code === process.env.VITE_TEST_COURSE_CODE! ? process.env.VITE_TEST_COURSE_TITLE! : `${code} Theory`,
        description: 'Test course for system verification',
        lecturer_id: lecturerData.user!.id,
        lecturer_name: process.env.VITE_TEST_LECTURER_NAME!,
        department: 'Computer Science',
        level: 400,
        total_students: 1
      });
      
      if (courseErr && courseErr.code !== '23505') {
        throw courseErr;
      }
      
      const { data: courseData } = await supabase.from('courses').select('id').eq('code', code).single();
      
      if (courseData) {
        const { error: enrollErr } = await supabase.from('course_enrollments').insert({
          course_id: courseData.id,
          student_id: studentData.user!.id
        });
        if (enrollErr && enrollErr.code !== '23505') throw enrollErr;
      }
    }
    console.log('Courses created and student enrolled.');

    console.log('\n--- Setup Complete! ---');

  } catch (err) {
    console.error('Setup failed:', err);
  }
}

setup();
