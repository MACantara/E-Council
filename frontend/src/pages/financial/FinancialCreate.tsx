import { CrudForm } from '@/components/Crud/CrudForm';
import { financialReports } from '@/config/resources';

export const FinancialCreate = () => <CrudForm config={financialReports} />;
