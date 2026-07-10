import { CrudForm } from '@/components/Crud/CrudForm';
import { conceptPapers } from '@/config/resources';

export const ConceptPapersEdit = () => <CrudForm config={conceptPapers} />;
