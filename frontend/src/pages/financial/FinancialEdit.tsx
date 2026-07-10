import { CrudForm } from '@/components/Crud/CrudForm';
import { financialReports } from '@/config/resources';

export const FinancialEdit = () => <CrudForm config={financialReports} />;
