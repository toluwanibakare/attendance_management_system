import re

# 1. Update AdminDashboard.tsx
with open('src/pages/admin/AdminDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Make Staff ID and Matric Number optional by removing validation
old_validation_1 = """    if (userForm.role === 'lecturer' && (!userForm.staffId.trim() || !userForm.department.trim())) {
      error('Lecturers require Staff ID and Department.');
      return;
    }"""
new_validation_1 = """    if (userForm.role === 'lecturer' && !userForm.department.trim()) {
      error('Lecturers require a Department.');
      return;
    }"""
content = content.replace(old_validation_1, new_validation_1)

old_validation_2 = """    if (userForm.role === 'student' && (!userForm.matricNumber.trim() || !userForm.department.trim())) {
      error('Students require Matric Number and Department.');
      return;
    }"""
new_validation_2 = """    if (userForm.role === 'student' && !userForm.department.trim()) {
      error('Students require a Department.');
      return;
    }"""
content = content.replace(old_validation_2, new_validation_2)

# Make UI labels indicate it's optional
old_staff_label = '<label className="mb-2 block text-sm font-medium text-muted-foreground">Staff ID</label>'
new_staff_label = '<label className="mb-2 block text-sm font-medium text-muted-foreground">Staff ID (Optional - Auto Generated)</label>'
content = content.replace(old_staff_label, new_staff_label)

old_matric_label = '<label className="mb-2 block text-sm font-medium text-muted-foreground">Matric Number</label>'
new_matric_label = '<label className="mb-2 block text-sm font-medium text-muted-foreground">Matric Number (Optional - Auto Generated)</label>'
content = content.replace(old_matric_label, new_matric_label)

# Add Print button next to Dashboard title
old_header = """        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <ShieldCheck className="w-8 h-8 text-primary" />
              Admin Portal
            </h1>
            <p className="text-muted-foreground mt-1">Manage university users, courses, and system settings.</p>
          </div>
        </div>"""

new_header = """        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 print-hide">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <ShieldCheck className="w-8 h-8 text-primary" />
              Admin Portal
            </h1>
            <p className="text-muted-foreground mt-1">Manage university users, courses, and system settings.</p>
          </div>
          <Button variant="outline" className="border-slate-700 bg-slate-800 text-white hover:bg-slate-700" onClick={() => window.print()}>
            Print Dashboard / PDF
          </Button>
        </div>"""
content = content.replace(old_header, new_header)

with open('src/pages/admin/AdminDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated AdminDashboard.tsx")

# 2. Add print styles to index.css
with open('src/index.css', 'a', encoding='utf-8') as f:
    f.write('''
/* Print Styles */
@media print {
  body {
    background: white !important;
    color: black !important;
  }
  .print-hide, nav, aside, button:not(.print-show) {
    display: none !important;
  }
  .glass-card, .bg-slate-900, .bg-slate-800 {
    background: transparent !important;
    border: 1px solid #ccc !important;
    box-shadow: none !important;
    color: black !important;
  }
  * {
    color: black !important;
    text-shadow: none !important;
  }
  h1, h2, h3, h4, h5, h6, p, span, div {
    color: black !important;
  }
  .text-white, .text-slate-400, .text-muted-foreground {
    color: black !important;
  }
  @page {
    margin: 1cm;
    size: A4 landscape;
  }
}
''')

print("Added print styles to index.css")

# Also add Print to LecturerDashboard.tsx
with open('src/pages/lecturer/LecturerDashboard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_header_lec = """        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <GraduationCap className="h-8 w-8 text-primary" />
              Lecturer Portal
            </h1>
            <p className="text-slate-400 mt-1">Manage your courses, view attendance, and start sessions.</p>
          </div>
        </div>"""

new_header_lec = """        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 print-hide">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <GraduationCap className="h-8 w-8 text-primary" />
              Lecturer Portal
            </h1>
            <p className="text-slate-400 mt-1">Manage your courses, view attendance, and start sessions.</p>
          </div>
          <Button variant="outline" className="border-slate-700 bg-slate-800 text-white hover:bg-slate-700" onClick={() => window.print()}>
            Print / Export to PDF
          </Button>
        </div>"""

content = content.replace(old_header_lec, new_header_lec)

with open('src/pages/lecturer/LecturerDashboard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated LecturerDashboard.tsx")
