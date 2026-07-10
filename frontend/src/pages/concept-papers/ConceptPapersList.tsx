import { CrudList } from '@/components/Crud/CrudList';
import { conceptPapers } from '@/config/resources';

export const ConceptPapersList = () => <CrudList config={conceptPapers} />;
