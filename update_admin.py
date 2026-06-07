import re
import sys

with open('src/pages/admin/AdminDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
content = content.replace('createLecturerByAdmin,', 'createUserByAdmin,')

# 2. Update state variables
content = content.replace('const [lecturerForm, setLecturerForm] = useState<LecturerFormState>(INITIAL_LECTURER_FORM);', 'const [userForm, setUserForm] = useState<UserFormState>(INITIAL_USER_FORM);')
content = content.replace('const [isSavingLecturer, setIsSavingLecturer] = useState(false);', 'const [isSavingUser, setIsSavingUser] = useState(false);')

# 3. Update handleSubmitLecturer function
old_handle_submit = """  const handleSubmitLecturer = async () => {
    if (!lecturerForm.fullName.trim() || !lecturerForm.email.trim() || !lecturerForm.password.trim() || !lecturerForm.staffId.trim() || !lecturerForm.department.trim()) {
      error('Fill in all required fields.');
      return;
    }
    
    if (lecturerForm.password.length < 8) {
      error('Password must be at least 8 characters.');
      return;
    }

    setIsSavingLecturer(true);
    const result = await createLecturerByAdmin({
      email: lecturerForm.email.trim(),
      password: lecturerForm.password,
      fullName: lecturerForm.fullName.trim(),
      role: 'lecturer',
      department: lecturerForm.department.trim(),
      staffId: lecturerForm.staffId.trim(),
      position: lecturerForm.position.trim(),
    });
    setIsSavingLecturer(false);

    if (!result.success) {
      error(result.message);
      return;
    }

    success(result.message);
    setLecturerForm(INITIAL_LECTURER_FORM);
    refreshManagementData();
  };"""

new_handle_submit = """  const handleSubmitUser = async () => {
    if (!userForm.fullName.trim() || !userForm.email.trim() || !userForm.password.trim()) {
      error('Fill in basic required fields (Name, Email, Password).');
      return;
    }
    
    if (userForm.role === 'lecturer' && (!userForm.staffId.trim() || !userForm.department.trim())) {
      error('Lecturers require Staff ID and Department.');
      return;
    }

    if (userForm.role === 'student' && (!userForm.matricNumber.trim() || !userForm.department.trim())) {
      error('Students require Matric Number and Department.');
      return;
    }
    
    if (userForm.password.length < 8) {
      error('Password must be at least 8 characters.');
      return;
    }

    setIsSavingUser(true);
    const result = await createUserByAdmin({
      email: userForm.email.trim(),
      password: userForm.password,
      fullName: userForm.fullName.trim(),
      role: userForm.role,
      department: userForm.department.trim(),
      staffId: userForm.role === 'lecturer' ? userForm.staffId.trim() : undefined,
      position: userForm.role === 'lecturer' ? userForm.position.trim() : undefined,
      matricNumber: userForm.role === 'student' ? userForm.matricNumber.trim() : undefined,
      level: userForm.role === 'student' ? parseInt(userForm.level, 10) : undefined,
    });
    setIsSavingUser(false);

    if (!result.success) {
      error(result.message);
      return;
    }

    success(result.message);
    setUserForm(INITIAL_USER_FORM);
    refreshManagementData();
  };"""

content = content.replace(old_handle_submit, new_handle_submit)

# 4. Update the JSX section
old_jsx_start = """                <div>
                  <h4 className="text-base font-semibold text-white">Create Lecturer</h4>
                  <p className="text-sm text-muted-foreground">Add a new lecturer account.</p>
                </div>"""

old_jsx_full_regex = re.compile(re.escape(old_jsx_start) + r'.*?Create Lecturer\s*</Button>\s*</div>', re.DOTALL)

new_jsx = """                <div>
                  <h4 className="text-base font-semibold text-white">Create User Account</h4>
                  <p className="text-sm text-muted-foreground">Add a new student, lecturer, or admin.</p>
                </div>
  
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="md:col-span-2">
                    <label className="mb-2 block text-sm font-medium text-muted-foreground">Account Role</label>
                    <select 
                      value={userForm.role}
                      onChange={(e) => setUserForm({ ...userForm, role: e.target.value as any })}
                      className="w-full bg-slate-800 border border-slate-700 text-white rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      <option value="student">Student</option>
                      <option value="lecturer">Lecturer</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-muted-foreground">Full Name</label>
                    <Input value={userForm.fullName} onChange={(e) => setUserForm({ ...userForm, fullName: e.target.value })} placeholder="John Doe" className="bg-slate-800 border-slate-700 text-white" />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-muted-foreground">Email</label>
                    <Input type="email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} placeholder="john.doe@lasustech.edu.ng" className="bg-slate-800 border-slate-700 text-white" />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-muted-foreground">Password</label>
                    <Input type="password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} placeholder="••••••••" className="bg-slate-800 border-slate-700 text-white" />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-muted-foreground">Department</label>
                    <Input value={userForm.department} onChange={(e) => setUserForm({ ...userForm, department: e.target.value })} placeholder="Computer Science" className="bg-slate-800 border-slate-700 text-white" />
                  </div>

                  {userForm.role === 'lecturer' && (
                    <>
                      <div>
                        <label className="mb-2 block text-sm font-medium text-muted-foreground">Staff ID</label>
                        <Input value={userForm.staffId} onChange={(e) => setUserForm({ ...userForm, staffId: e.target.value })} placeholder="LEC/001" className="bg-slate-800 border-slate-700 text-white" />
                      </div>
                      <div>
                        <label className="mb-2 block text-sm font-medium text-muted-foreground">Position</label>
                        <Input value={userForm.position} onChange={(e) => setUserForm({ ...userForm, position: e.target.value })} placeholder="Senior Lecturer" className="bg-slate-800 border-slate-700 text-white" />
                      </div>
                    </>
                  )}

                  {userForm.role === 'student' && (
                    <>
                      <div>
                        <label className="mb-2 block text-sm font-medium text-muted-foreground">Matric Number</label>
                        <Input value={userForm.matricNumber} onChange={(e) => setUserForm({ ...userForm, matricNumber: e.target.value })} placeholder="MAT/001" className="bg-slate-800 border-slate-700 text-white" />
                      </div>
                      <div>
                        <label className="mb-2 block text-sm font-medium text-muted-foreground">Level</label>
                        <select 
                          value={userForm.level}
                          onChange={(e) => setUserForm({ ...userForm, level: e.target.value })}
                          className="w-full bg-slate-800 border border-slate-700 text-white rounded-md p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                          <option value="100">100 Level</option>
                          <option value="200">200 Level</option>
                          <option value="300">300 Level</option>
                          <option value="400">400 Level</option>
                          <option value="500">500 Level</option>
                        </select>
                      </div>
                    </>
                  )}
                </div>
  
                <Button onClick={handleSubmitUser} disabled={isSavingUser} className="w-full bg-primary mt-2">
                  {isSavingUser ? 'Creating...' : 'Create Account'}
                </Button>
              </div>"""

content = old_jsx_full_regex.sub(new_jsx, content)

with open('src/pages/admin/AdminDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done updating AdminDashboard.tsx")
