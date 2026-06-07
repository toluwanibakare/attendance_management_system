import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://sqajcadckudelyoobymc.supabase.co'; // using the project ID I already know
const SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNxYWpjYWRja3VkZWx5b29ieW1jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDY5NTQ3MCwiZXhwIjoyMDk2MjcxNDcwfQ.Q5C3K2Lz_1We0tSv1HXXOpPe5H5szIS8G1vUAM6_N1g';

const adminClient = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

async function run() {
  console.log('Attempting to create a test lecturer...');
  const metadata = {
    full_name: 'Test Lecturer',
    role: 'lecturer',
    department: 'Computer Science',
    staff_id: 'STAFF-12345',
    position: 'Senior Lecturer',
  };

  const { data, error } = await adminClient.auth.admin.createUser({
    email: 'test.lecturer@lasustech.edu.ng',
    password: 'password123',
    email_confirm: true,
    user_metadata: metadata,
  });

  if (error) {
    console.error('ERROR CREATING USER:', JSON.stringify(error, null, 2));
  } else {
    console.log('SUCCESS CREATING USER:', data.user.id);
  }
}

run();
