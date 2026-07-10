import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { CrudDetail } from '@/components/Crud/CrudDetail';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { FileUpload } from '@/components/ui/FileUpload';
import { events } from '@/config/resources';
import { createTransaction, updateTransaction, type TransactionPayload } from '@/api/uploads';

interface Transaction {
  transaction_id: number;
  transaction_name: string;
  transaction_date?: string;
  unit_amount?: number;
  unit_price?: number;
  total?: number;
  category?: string;
  type?: 'Income' | 'Expense';
  receipt_url?: string | null;
}

export const EventsDetail = () => {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<number | null>(null);

  const handleSave = async (eventId: string, transaction: Transaction, file?: File) => {
    const payload: TransactionPayload = {
      transaction_name: transaction.transaction_name,
      transaction_date: transaction.transaction_date,
      unit_amount: transaction.unit_amount,
      unit_price: transaction.unit_price,
      total: transaction.total,
      category: transaction.category,
      type: transaction.type,
    };

    try {
      if (editingId === transaction.transaction_id) {
        await updateTransaction(eventId, String(transaction.transaction_id), payload, file);
        toast.success('Transaction updated');
      } else {
        await createTransaction(eventId, payload, file);
        toast.success('Transaction created');
      }
      queryClient.invalidateQueries({ queryKey: [events.endpoint, eventId] });
      setEditingId(null);
    } catch (error) {
      toast.error((error as Error)?.message || 'Transaction failed');
    }
  };

  return (
    <div className="space-y-6">
      <CrudDetail
        config={events}
        renderExtra={(item) => {
          const eventId = String(item[events.idField]);
          const transactions = (item.transactions as Transaction[]) ?? [];

          return (
            <div className="mt-8 border-t border-gray-200 pt-6 dark:border-gray-700">
              <h3 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
                Transactions
              </h3>

              {transactions.length === 0 ? (
                <p className="text-sm text-gray-600 dark:text-gray-300">No transactions yet.</p>
              ) : (
                <div className="space-y-4">
                  {transactions.map((transaction) => (
                    <TransactionRow
                      key={transaction.transaction_id}
                      eventId={eventId}
                      transaction={transaction}
                      isEditing={editingId === transaction.transaction_id}
                      onEdit={() => setEditingId(transaction.transaction_id)}
                      onCancel={() => setEditingId(null)}
                      onSave={(t, file) => handleSave(eventId, t, file)}
                    />
                  ))}
                </div>
              )}

              <div className="mt-6">
                <h4 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Add Transaction
                </h4>
                <TransactionForm onSave={(t, file) => handleSave(eventId, t, file)} />
              </div>
            </div>
          );
        }}
      />
    </div>
  );
};

interface TransactionFormProps {
  transaction?: Transaction;
  onSave: (transaction: Transaction, file?: File) => void;
  onCancel?: () => void;
}

const TransactionForm = ({ transaction, onSave, onCancel }: TransactionFormProps) => {
  const [name, setName] = useState(transaction?.transaction_name ?? '');
  const [amount, setAmount] = useState(transaction?.unit_amount ?? 0);
  const [price, setPrice] = useState(transaction?.unit_price ?? 0);
  const [type, setType] = useState<'Income' | 'Expense'>(transaction?.type ?? 'Expense');
  const [file, setFile] = useState<File | undefined>();

  const total = amount * price;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(
      {
        transaction_id: transaction?.transaction_id ?? 0,
        transaction_name: name,
        unit_amount: Number(amount),
        unit_price: Number(price),
        total,
        type,
      },
      file
    );
  };

  return (
    <Card className="p-4">
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <Input
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            type="number"
            placeholder="Quantity"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            required
          />
          <Input
            type="number"
            step="0.01"
            placeholder="Unit price"
            value={price}
            onChange={(e) => setPrice(Number(e.target.value))}
            required
          />
          <select
            value={type}
            onChange={(e) => setType(e.target.value as 'Income' | 'Expense')}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          >
            <option value="Income">Income</option>
            <option value="Expense">Expense</option>
          </select>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Total: {total.toFixed(2)}
          </span>
          <FileUpload
            accept="image/*,.pdf"
            label="Receipt"
            onUpload={(selected) => setFile(selected)}
          />
        </div>
        <div className="flex gap-2">
          <Button type="submit" size="sm">
            {transaction ? 'Update' : 'Add'}
          </Button>
          {onCancel && (
            <Button type="button" variant="secondary" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>
      </form>
    </Card>
  );
};

interface TransactionRowProps {
  eventId: string;
  transaction: Transaction;
  isEditing: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave: (transaction: Transaction, file?: File) => void;
}

const TransactionRow = ({
  transaction,
  isEditing,
  onEdit,
  onCancel,
  onSave,
}: TransactionRowProps) => {
  if (isEditing) {
    return <TransactionForm transaction={transaction} onSave={onSave} onCancel={onCancel} />;
  }

  return (
    <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-700">
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{transaction.transaction_name}</p>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          {transaction.type} — {transaction.total?.toFixed(2)}
        </p>
        {transaction.receipt_url && (
          <a
            href={transaction.receipt_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-violet-600 hover:underline"
          >
            View receipt
          </a>
        )}
      </div>
      <Button variant="secondary" size="sm" onClick={onEdit}>
        Edit
      </Button>
    </div>
  );
};
