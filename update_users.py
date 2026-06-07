import re

with open('src/pages/admin/AdminDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
content = content.replace(
    'createUserByAdmin,', 
    'createUserByAdmin,\n  updateUserByAdmin,\n  deleteUserByAdmin,'
)

content = content.replace(
    "import { Edit, Plus, Trash2 } from 'lucide-react';",
    "import { Edit, Plus, Trash2, Search, Filter } from 'lucide-react';"
)

# 2. Add state for editingUserId and search term for users
state_insert_point = "  const [userForm, setUserForm] = useState<UserFormState>(INITIAL_USER_FORM);"
new_state = """  const [userForm, setUserForm] = useState<UserFormState>(INITIAL_USER_FORM);
  const [editingUserId, setEditingUserId] = useState<string>('');
  const [userSearchQuery, setUserSearchQuery] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState<'all' | 'student' | 'lecturer' | 'admin'>('all');"""
content = content.replace(state_insert_point, new_state)

# 3. Update handleSubmitUser
old_submit = """  const handleSubmitUser = async () => {
    if (!userForm.fullName.trim() || !userForm.email.trim() || !userForm.password.trim()) {
      error('Fill in basic required fields (Name, Email, Password).');
      return;
    }"""
new_submit = """  const handleSubmitUser = async () => {
    if (!userForm.fullName.trim() || !userForm.email.trim() || (!editingUserId && !userForm.password.trim())) {
      error('Fill in basic required fields (Name, Email). Password is required for new accounts.');
      return;
    }"""
content = content.replace(old_submit, new_submit)

old_api_call = """    setIsSavingUser(true);
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
    setIsSavingUser(false);"""
new_api_call = """    setIsSavingUser(true);
    const payload = {
      email: userForm.email.trim(),
      password: userForm.password || undefined,
      fullName: userForm.fullName.trim(),
      role: userForm.role,
      department: userForm.department.trim(),
      staffId: userForm.role === 'lecturer' ? userForm.staffId.trim() : undefined,
      position: userForm.role === 'lecturer' ? userForm.position.trim() : undefined,
      matricNumber: userForm.role === 'student' ? userForm.matricNumber.trim() : undefined,
      level: userForm.role === 'student' ? parseInt(userForm.level, 10) : undefined,
    };
    
    const result = editingUserId 
      ? await updateUserByAdmin(editingUserId, payload)
      : await createUserByAdmin(payload as any);
      
    setIsSavingUser(false);"""
content = content.replace(old_api_call, new_api_call)

old_success = """    success(result.message);
    setUserForm(INITIAL_USER_FORM);"""
new_success = """    success(result.message);
    setUserForm(INITIAL_USER_FORM);
    setEditingUserId('');"""
content = content.replace(old_success, new_success)


# 4. Add handlers for edit and delete
handlers_insert = """  const handleDeleteSelectedCourse = async () => {"""
new_handlers = """  const handleEditUser = (user: any, role: string) => {
    setEditingUserId(user.id);
    setUserForm({
      role: role as any,
      fullName: user.name,
      email: user.email,
      password: '', // Leave blank when editing
      department: user.department || '',
      staffId: user.staffId || '',
      position: user.position || '',
      matricNumber: user.matricNumber || '',
      level: user.level?.toString() || '100',
    });
    window.scrollTo({ top: document.getElementById('user-management-section')?.offsetTop, behavior: 'smooth' });
  };

  const handleDeleteUser = async (userId: string, name: string) => {
    if (!window.confirm(`Are you sure you want to completely delete ${name}? This action cannot be undone and will delete all their data.`)) {
      return;
    }
    const result = await deleteUserByAdmin(userId);
    if (!result.success) {
      error(result.message);
      return;
    }
    success(result.message);
    refreshManagementData();
  };

  const allUsersList = useMemo(() => {
    let list = [
      ...students.map(s => ({ ...s, role: 'student' })),
      ...lecturers.map(l => ({ ...l, role: 'lecturer' }))
    ];
    
    if (userRoleFilter !== 'all') {
      list = list.filter(u => u.role === userRoleFilter);
    }
    if (userSearchQuery.trim()) {
      const q = userSearchQuery.toLowerCase();
      list = list.filter(u => u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
    }
    return list;
  }, [students, lecturers, userSearchQuery, userRoleFilter]);

  const handleDeleteSelectedCourse = async () => {"""
content = content.replace(handlers_insert, new_handlers)

# 5. Add "Cancel Edit" button and ID to section
content = content.replace(
    'className="space-y-6 mt-6"',
    'id="user-management-section" className="space-y-6 mt-6"'
)

old_submit_btn = """              <Button onClick={handleSubmitUser} disabled={isSavingUser} className="w-full bg-primary mt-2">
                {isSavingUser ? 'Creating...' : 'Create Account'}
              </Button>"""
new_submit_btn = """              <div className="flex gap-2 mt-2">
                <Button onClick={handleSubmitUser} disabled={isSavingUser} className="flex-1 bg-primary">
                  {isSavingUser ? 'Saving...' : editingUserId ? 'Update Account' : 'Create Account'}
                </Button>
                {editingUserId && (
                  <Button variant="outline" className="border-slate-700 bg-slate-800 text-white" onClick={() => { setEditingUserId(''); setUserForm(INITIAL_USER_FORM); }}>
                    Cancel
                  </Button>
                )}
              </div>"""
content = content.replace(old_submit_btn, new_submit_btn)

# 6. Add "Users Directory" table
old_stats_grid = """      {/* Stats Grid */}"""
new_users_table = """
      {/* Existing Users Directory */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="space-y-4 mt-8"
      >
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-primary" />
            Users Directory
          </h3>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search users..."
                value={userSearchQuery}
                onChange={(e) => setUserSearchQuery(e.target.value)}
                className="pl-9 bg-slate-800/50 border-white/10 text-white w-full"
              />
            </div>
            <select
              value={userRoleFilter}
              onChange={(e) => setUserRoleFilter(e.target.value as any)}
              className="bg-slate-800 border border-white/10 text-white rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary h-10"
            >
              <option value="all">All Roles</option>
              <option value="student">Students</option>
              <option value="lecturer">Lecturers</option>
            </select>
          </div>
        </div>

        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead className="text-muted-foreground">Name</TableHead>
                  <TableHead className="text-muted-foreground">Email</TableHead>
                  <TableHead className="text-muted-foreground">Role</TableHead>
                  <TableHead className="text-muted-foreground">Department</TableHead>
                  <TableHead className="text-muted-foreground text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {allUsersList.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                      No users found.
                    </TableCell>
                  </TableRow>
                ) : (
                  allUsersList.map((user) => (
                    <TableRow key={user.id} className="border-white/10 hover:bg-white/5">
                      <TableCell className="font-medium text-white">{user.name}</TableCell>
                      <TableCell className="text-slate-300">{user.email}</TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          user.role === 'student' ? 'bg-blue-500/20 text-blue-400' :
                          user.role === 'lecturer' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {user.role}
                        </span>
                      </TableCell>
                      <TableCell className="text-slate-300">{user.department}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white" onClick={() => handleEditUser(user, user.role)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-red-400 hover:bg-red-400/10" onClick={() => handleDeleteUser(user.id, user.name)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </motion.section>

      {/* Stats Grid */}"""
content = content.replace(old_stats_grid, new_users_table)

with open('src/pages/admin/AdminDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated AdminDashboard.tsx to include Users Directory and actions")
