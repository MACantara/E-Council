import { Routes, Route } from 'react-router-dom';
import { RootLayout } from '@/components/layout/RootLayout';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';

import { Login } from '@/pages/auth/Login';
import { Register } from '@/pages/auth/Register';
import { ForgotPassword } from '@/pages/auth/ForgotPassword';
import { ResetPassword } from '@/pages/auth/ResetPassword';

import { Dashboard } from '@/pages/dashboard/Dashboard';

import { ConceptPapersList } from '@/pages/concept-papers/ConceptPapersList';
import { ConceptPapersCreate } from '@/pages/concept-papers/ConceptPapersCreate';
import { ConceptPapersEdit } from '@/pages/concept-papers/ConceptPapersEdit';
import { ConceptPapersDetail } from '@/pages/concept-papers/ConceptPapersDetail';

import { EventsList } from '@/pages/events/EventsList';
import { EventsCreate } from '@/pages/events/EventsCreate';
import { EventsEdit } from '@/pages/events/EventsEdit';
import { EventsDetail } from '@/pages/events/EventsDetail';

import { MeetingsList } from '@/pages/meetings/MeetingsList';
import { MeetingsCreate } from '@/pages/meetings/MeetingsCreate';
import { MeetingsEdit } from '@/pages/meetings/MeetingsEdit';
import { MeetingsDetail } from '@/pages/meetings/MeetingsDetail';

import { BoardResolutionsList } from '@/pages/board-resolutions/BoardResolutionsList';
import { BoardResolutionsCreate } from '@/pages/board-resolutions/BoardResolutionsCreate';
import { BoardResolutionsEdit } from '@/pages/board-resolutions/BoardResolutionsEdit';
import { BoardResolutionsDetail } from '@/pages/board-resolutions/BoardResolutionsDetail';

import { FinancialList } from '@/pages/financial/FinancialList';
import { FinancialCreate } from '@/pages/financial/FinancialCreate';
import { FinancialEdit } from '@/pages/financial/FinancialEdit';
import { FinancialDetail } from '@/pages/financial/FinancialDetail';

import { DocumentationList } from '@/pages/documentation/DocumentationList';
import { DocumentationCreate } from '@/pages/documentation/DocumentationCreate';
import { DocumentationEdit } from '@/pages/documentation/DocumentationEdit';
import { DocumentationDetail } from '@/pages/documentation/DocumentationDetail';

import { Profile } from '@/pages/account/Profile';
import { UserList } from '@/pages/admin/UserList';
import { AuditLogs } from '@/pages/admin/AuditLogs';

const withAuth = (element: React.ReactNode) => <ProtectedRoute>{element}</ProtectedRoute>;
const withAdmin = (element: React.ReactNode) => <ProtectedRoute requireAdmin>{element}</ProtectedRoute>;

export const AppRoutes = () => (
  <Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/register" element={<Register />} />
    <Route path="/forgot-password" element={<ForgotPassword />} />
    <Route path="/reset-password/:selector/:token" element={<ResetPassword />} />

    <Route element={<RootLayout />}>
      <Route path="/" element={withAuth(<Dashboard />)} />

      <Route path="/concept-papers" element={withAuth(<ConceptPapersList />)} />
      <Route path="/concept-papers/create" element={withAuth(<ConceptPapersCreate />)} />
      <Route path="/concept-papers/:id" element={withAuth(<ConceptPapersDetail />)} />
      <Route path="/concept-papers/:id/edit" element={withAuth(<ConceptPapersEdit />)} />

      <Route path="/events" element={withAuth(<EventsList />)} />
      <Route path="/events/create" element={withAuth(<EventsCreate />)} />
      <Route path="/events/:id" element={withAuth(<EventsDetail />)} />
      <Route path="/events/:id/edit" element={withAuth(<EventsEdit />)} />

      <Route path="/meetings" element={withAuth(<MeetingsList />)} />
      <Route path="/meetings/create" element={withAuth(<MeetingsCreate />)} />
      <Route path="/meetings/:id" element={withAuth(<MeetingsDetail />)} />
      <Route path="/meetings/:id/edit" element={withAuth(<MeetingsEdit />)} />

      <Route path="/board-resolutions" element={withAuth(<BoardResolutionsList />)} />
      <Route path="/board-resolutions/create" element={withAuth(<BoardResolutionsCreate />)} />
      <Route path="/board-resolutions/:id" element={withAuth(<BoardResolutionsDetail />)} />
      <Route path="/board-resolutions/:id/edit" element={withAuth(<BoardResolutionsEdit />)} />

      <Route path="/financial-reports" element={withAuth(<FinancialList />)} />
      <Route path="/financial-reports/create" element={withAuth(<FinancialCreate />)} />
      <Route path="/financial-reports/:id" element={withAuth(<FinancialDetail />)} />
      <Route path="/financial-reports/:id/edit" element={withAuth(<FinancialEdit />)} />

      <Route path="/documentation" element={withAuth(<DocumentationList />)} />
      <Route path="/documentation/create" element={withAuth(<DocumentationCreate />)} />
      <Route path="/documentation/:id" element={withAuth(<DocumentationDetail />)} />
      <Route path="/documentation/:id/edit" element={withAuth(<DocumentationEdit />)} />

      <Route path="/account/profile" element={withAuth(<Profile />)} />

      <Route path="/admin/users" element={withAdmin(<UserList />)} />
      <Route path="/admin/audit-logs" element={withAdmin(<AuditLogs />)} />
    </Route>
  </Routes>
);
