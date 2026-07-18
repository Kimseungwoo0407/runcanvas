import { lazy, Suspense } from 'react';
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import { LoadingBlock } from '../components/LoadingBlock';
import { Layout } from './Layout';
import { ProtectedRoute } from './ProtectedRoute';

const AdminPage = lazy(() => import('../pages/AdminPage').then((module) => ({ default: module.AdminPage })));
const BuilderPage = lazy(() => import('../pages/BuilderPage').then((module) => ({ default: module.BuilderPage })));
const CoursePage = lazy(() => import('../pages/CoursePage').then((module) => ({ default: module.CoursePage })));
const DashboardPage = lazy(() => import('../pages/DashboardPage').then((module) => ({ default: module.DashboardPage })));
const JobPage = lazy(() => import('../pages/JobPage').then((module) => ({ default: module.JobPage })));
const LoginPage = lazy(() => import('../pages/LoginPage').then((module) => ({ default: module.LoginPage })));
const SettingsPage = lazy(() => import('../pages/SettingsPage').then((module) => ({ default: module.SettingsPage })));
const SharedCoursePage = lazy(() =>
  import('../pages/SharedCoursePage').then((module) => ({ default: module.SharedCoursePage })),
);

export function App() {
  return (
    <HashRouter>
      <Suspense fallback={<LoadingBlock label="화면을 불러오는 중" />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/shared/:token" element={<SharedCoursePage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="builder" element={<BuilderPage />} />
              <Route path="jobs/:jobId" element={<JobPage />} />
              <Route path="courses/:courseId" element={<CoursePage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="admin" element={<AdminPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </HashRouter>
  );
}
