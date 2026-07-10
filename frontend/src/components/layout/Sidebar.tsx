import { Link } from 'react-router-dom';
import { useAuth } from '@/providers/AuthProvider';
import {
  LayoutDashboard,
  FileText,
  Calendar,
  Users,
  ClipboardList,
  Banknote,
  FolderOpen,
  UserCircle,
  Shield,
} from 'lucide-react';

export const Sidebar = () => {
  const { isAuthenticated, isAdmin } = useAuth();

  const links = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/concept-papers', label: 'Concept Papers', icon: FileText },
    { to: '/events', label: 'Events', icon: Calendar },
    { to: '/meetings', label: 'Meetings', icon: Users },
    { to: '/board-resolutions', label: 'Board Resolutions', icon: ClipboardList },
    { to: '/financial-reports', label: 'Financial Reports', icon: Banknote },
    { to: '/documentation', label: 'Documentation', icon: FolderOpen },
    { to: '/account/profile', label: 'Account', icon: UserCircle },
    ...(isAdmin ? [{ to: '/admin/users', label: 'Admin', icon: Shield }] : []),
  ];

  if (!isAuthenticated) return null;

  return (
    <aside className="hidden w-64 flex-col border-r border-gray-200 bg-white md:flex">
      <nav className="flex-1 space-y-1 p-4">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <Link
              key={link.to}
              to={link.to}
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
            >
              <Icon className="h-5 w-5" />
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
};
