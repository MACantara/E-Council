import { CrudForm } from '@/components/Crud/CrudForm';
import { meetings } from '@/config/resources';

export const MeetingsEdit = () => <CrudForm config={meetings} />;
