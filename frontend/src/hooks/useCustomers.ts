import { useCallback, useEffect, useState } from 'react';

import { listCustomers } from '../api/modules/customers';
import { useAuth } from '../auth/AuthProvider';
import type { Customer } from '../types';

function toCustomer(customer: Awaited<ReturnType<typeof listCustomers>>['items'][number]): Customer {
  return {
    id: customer.id,
    name: customer.fullName,
    phone: customer.phone ?? '—',
    address: [customer.address, customer.district].filter(Boolean).join(', ') || '—',
    totalPurchases: 0,
    lastOrder: '—',
  };
}

export function useCustomers() {
  const auth = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!auth || auth.loading || (auth.session && !auth.profile)) return;
    if (!auth.session || !auth.profile || !['admin', 'operator'].includes(auth.profile.role)) {
      setCustomers([]);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const first = await listCustomers(1, 100);
      const pages = Math.ceil(first.total / first.pageSize);
      const remaining = pages > 1
        ? await Promise.all(
          Array.from({ length: pages - 1 }, (_, index) => listCustomers(index + 2, 100)),
        )
        : [];
      setCustomers([...first.items, ...remaining.flatMap((page) => page.items)].map(toCustomer));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No pudimos cargar los clientes.');
    } finally {
      setLoading(false);
    }
  }, [auth?.loading, auth?.profile, auth?.session]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { customers, loading, error, reload };
}
