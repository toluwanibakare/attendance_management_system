-- Fix infinite recursion in RLS policies by using SECURITY DEFINER functions to bypass RLS for role checks

create or replace function public.is_admin()
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  is_adm boolean;
begin
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and role = 'admin'
  ) into is_adm;
  return coalesce(is_adm, false);
end;
$$;

create or replace function public.is_lecturer_or_admin()
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  is_valid boolean;
begin
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and role in ('lecturer', 'admin')
  ) into is_valid;
  return coalesce(is_valid, false);
end;
$$;

-- Drop all recursive policies
drop policy if exists "profiles_select_own" on public.profiles;
drop policy if exists "student_profiles_select_own" on public.student_profiles;
drop policy if exists "lecturer_profiles_select_own" on public.lecturer_profiles;
drop policy if exists "admin_profiles_select_own" on public.admin_profiles;
drop policy if exists "courses_manage_own_lecturer" on public.courses;
drop policy if exists "course_schedules_manage_own" on public.course_schedules;
drop policy if exists "course_enrollments_select_authenticated" on public.course_enrollments;
drop policy if exists "course_enrollments_insert_admin_or_lecturer" on public.course_enrollments;
drop policy if exists "attendance_sessions_manage_own" on public.attendance_sessions;
drop policy if exists "attendance_sessions_update_own" on public.attendance_sessions;
drop policy if exists "attendance_records_select_own_or_admin" on public.attendance_records;
drop policy if exists "audit_logs_admin_only" on public.audit_logs;
drop policy if exists "bluetooth_verifications_select_own_or_admin" on public.bluetooth_verifications;

-- Recreate policies using the new functions
create policy "profiles_select_own" on public.profiles
  for select to authenticated
  using (auth.uid() = id or public.is_admin());

create policy "student_profiles_select_own" on public.student_profiles
  for select to authenticated
  using (auth.uid() = user_id or public.is_admin());

create policy "lecturer_profiles_select_own" on public.lecturer_profiles
  for select to authenticated
  using (auth.uid() = user_id or public.is_admin());

create policy "admin_profiles_select_own" on public.admin_profiles
  for select to authenticated
  using (auth.uid() = user_id or public.is_admin());

create policy "courses_manage_own_lecturer" on public.courses
  for all to authenticated
  using (auth.uid() = lecturer_id or public.is_admin())
  with check (auth.uid() = lecturer_id or public.is_admin());

create policy "course_schedules_manage_own" on public.course_schedules
  for all to authenticated
  using (
    exists (
      select 1 from public.courses c 
      where c.id = course_id and (c.lecturer_id = auth.uid() or public.is_admin())
    )
  );

create policy "course_enrollments_select_authenticated" on public.course_enrollments
  for select to authenticated
  using (auth.uid() = student_id or public.is_lecturer_or_admin());

create policy "course_enrollments_insert_admin_or_lecturer" on public.course_enrollments
  for insert to authenticated
  with check (public.is_lecturer_or_admin());

create policy "attendance_sessions_manage_own" on public.attendance_sessions
  for insert to authenticated
  with check (auth.uid() = lecturer_id or public.is_admin());

create policy "attendance_sessions_update_own" on public.attendance_sessions
  for update to authenticated
  using (auth.uid() = lecturer_id or public.is_admin())
  with check (auth.uid() = lecturer_id or public.is_admin());

create policy "attendance_records_select_own_or_admin" on public.attendance_records
  for select to authenticated
  using (
    auth.uid() = student_id 
    or public.is_admin() 
    or exists (
      select 1 from public.courses c 
      where c.id = (select s.course_id from public.attendance_sessions s where s.id = session_id) 
      and c.lecturer_id = auth.uid()
    )
  );

create policy "audit_logs_admin_only" on public.audit_logs
  for all to authenticated
  using (public.is_admin());

create policy "bluetooth_verifications_select_own_or_admin" on public.bluetooth_verifications
  for select to authenticated
  using (
    auth.uid() = student_id 
    or public.is_admin() 
    or exists (
      select 1 from public.courses c 
      where c.id = (select s.course_id from public.attendance_sessions s where s.id = session_id) 
      and c.lecturer_id = auth.uid()
    )
  );
