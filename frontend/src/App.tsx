import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';

// Layout
import { AppLayout } from './components/layout/AppLayout';

// Core Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';

// Dashboard Pages
import Dashboard from './pages/Dashboard';
import AdminDashboard from './pages/admin/AdminDashboard';
import Analytics from './pages/admin/Analytics';

// Feature Pages
import Chat from './pages/Chat';
import Search from './pages/Search';
import Notices from './pages/Notices';
import Resources from './pages/Resources';
import PdfQA from './pages/PdfQA';
import Attendance from './pages/Attendance';
import Marks from './pages/Marks';
import Fees from './pages/Fees';

// Management Pages
import DocumentManager from './pages/admin/DocumentManager';
import UserManager from './pages/admin/UserManager';
import NoticeInbox from './pages/admin/NoticeInbox';
import NoticeInboxDetail from './pages/admin/NoticeInboxDetail';

import { getAuthToken } from './lib/auth';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = getAuthToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected Routes wrapped in AppLayout */}
        <Route path="/" element={<ProtectedRoute><AppLayout><Outlet /></AppLayout></ProtectedRoute>}>
          {/* General routes */}
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="profile" element={<Profile />} />
          <Route path="chat" element={<Chat />} />
          <Route path="search" element={<Search />} />
          <Route path="notices" element={<Notices />} />
          <Route path="resources" element={<Resources />} />
          <Route path="pdf-qa" element={<PdfQA />} />
          <Route path="attendance" element={<Attendance />} />
          <Route path="marks" element={<Marks />} />
          <Route path="fees" element={<Fees />} />

          {/* Admin routes */}
          <Route path="admin/dashboard" element={<AdminDashboard />} />
          <Route path="admin/docs" element={<DocumentManager />} />
          <Route path="admin/users" element={<UserManager />} />
          <Route path="admin/analytics" element={<Analytics />} />
          <Route path="admin/notice-inbox" element={<NoticeInbox />} />
          <Route path="admin/notice-inbox/:id" element={<NoticeInboxDetail />} />
        </Route>
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
