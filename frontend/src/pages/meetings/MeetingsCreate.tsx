import { CrudForm } from '@/components/Crud/CrudForm';
import { meetings } from '@/config/resources';

export const MeetingsCreate = () => <CrudForm config={meetings} />;
