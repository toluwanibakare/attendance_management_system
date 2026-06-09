import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://sqajcadckudelyoobymc.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNxYWpjYWRja3VkZWx5b29ieW1jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDY5NTQ3MCwiZXhwIjoyMDk2MjcxNDcwfQ.Q5C3K2Lz_1We0tSv1HXXOpPe5H5szIS8G1vUAM6_N1g';

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

async function resetAdminPassword() {
  const { data: usersData, error: usersError } = await supabase.auth.admin.listUsers();
  if (usersError) {
    console.error('Error fetching users:', usersError);
    return;
  }

  const adminUser = usersData.users.find(u => u.email === 'admin@lasustech.edu.ng');
  if (!adminUser) {
    console.log('Admin user not found!');
    return;
  }

  const { data, error } = await supabase.auth.admin.updateUserById(adminUser.id, {
    password: 'Password123!',
  });

  if (error) {
    console.error('Failed to reset password:', error);
  } else {
    console.log('Successfully reset admin@lasustech.edu.ng password to: Password123!');
  }
}

resetAdminPassword();
