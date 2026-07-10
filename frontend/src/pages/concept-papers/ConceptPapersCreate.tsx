import { CrudForm } from '@/components/Crud/CrudForm';
import { conceptPapers } from '@/config/resources';

export const ConceptPapersCreate = () => <CrudForm config={conceptPapers} />;
