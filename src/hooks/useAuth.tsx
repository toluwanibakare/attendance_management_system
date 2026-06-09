import { useEffect, useState, useCallback, type ReactNode } from 'react';
import type { User, UserRole } from '@/types';
import { isSupabaseConfigured, supabase } from '@/lib/supabase/client';
import { authenticateUser, changeUserPassword, registerUser, restoreAuthenticatedUser, signOutUser, updateProfileInDatabase } from '@/services/universityService';
import { AuthContext, type RegisterInput, type RegisterOutcome } from '@/hooks/auth-context';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) {
      setIsInitializing(false);
      return;
    }

    let isMounted = true;

    // First load: Try to get existing session
    const loadInitialSession = async () => {
      try {
        const restoredUser = await restoreAuthenticatedUser();
        if (isMounted) {
          setUser(restoredUser);
        }
      } catch (e) {
        console.error("Failed to restore auth session:", e);
      } finally {
        if (isMounted) setIsInitializing(false);
      }
    };

    void loadInitialSession();

    // Listen for ongoing changes (login/logout from this or other tabs)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (!isMounted) return;

      if (event === 'SIGNED_OUT' || !session?.user) {
        setUser(null);
        return;
      }

      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED' || event === 'USER_UPDATED') {
        try {
          const restoredUser = await restoreAuthenticatedUser();
          if (isMounted) {
            setUser(restoredUser);
          }
        } catch (e) {
          console.error("Auth state change error:", e);
        }
      }
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const login = useCallback(async (email: string, _password: string, role: UserRole): Promise<boolean> => {
    setIsLoading(true);
    setAuthError(null);

    try {
      const { user: authenticatedUser, message } = await authenticateUser(email, _password, role);

      if (!authenticatedUser) {
        setAuthError(message || 'Invalid credentials.');
        return false;
      }
      
      // We don't set user manually here; we let onAuthStateChange do it to avoid race conditions
      // However, we must wait for it if we want to navigate smoothly. 
      // Fortunately, authenticateUser now awaits loadSupabaseUser internally,
      // so we can set it here purely to immediately satisfy ProtectedRoute.
      setUser(authenticatedUser);
      return true;
    } catch (error: any) {
      setAuthError(error?.message || 'An unexpected error occurred during login.');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (input: RegisterInput): Promise<RegisterOutcome> => {
    setIsLoading(true);
    setAuthError(null);

    try {
      const result = await registerUser(input);

      if (result.errorCode) {
        setAuthError(result.message ?? 'Unable to create account.');
        return {
          success: false,
          needsEmailConfirmation: false,
          message: result.message,
        };
      }

      if (result.user && !result.needsEmailConfirmation) {
        setUser(result.user);
      }

      return {
        success: true,
        needsEmailConfirmation: result.needsEmailConfirmation,
        message: result.message,
      };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await signOutUser();
    } catch (e) {
      console.warn("Sign out error", e);
    } finally {
      // Allow onAuthStateChange to clear the user to prevent deadlocks,
      // but clear it here as a fallback in case the event is delayed.
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  const updateUserProfile = useCallback(async (updates: Partial<Pick<User, 'name' | 'email' | 'department' | 'avatar'>>) => {
    if (!user) return null;

    const updatedUser = await updateProfileInDatabase(user, updates);

    if (updatedUser) {
      setUser(updatedUser);
    }

    return updatedUser;
  }, [user]);

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    if (!user) {
      return {
        success: false,
        message: 'You must be signed in to change your password.',
      };
    }

    return changeUserPassword(currentPassword, newPassword);
  }, [user]);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      login,
      register,
      logout,
      updateUserProfile,
      changePassword,
      isLoading,
      isInitializing,
      authError
    }}>
      {children}
    </AuthContext.Provider>
  );
}
