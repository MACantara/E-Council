import { CrudList } from '@/components/Crud/CrudList';
import { meetings } from '@/config/resources';

export const MeetingsList = () => <CrudList config={meetings} />;
