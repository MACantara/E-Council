import { CrudList } from '@/components/Crud/CrudList';
import { financialReports } from '@/config/resources';

export const FinancialList = () => <CrudList config={financialReports} />;
