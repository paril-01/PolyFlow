import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

interface OrderHistoryListProps {
  onComplete?: (data: any) => void;
}

export const OrderHistoryList: React.FC<OrderHistoryListProps> = ({ onComplete }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleOrderHistoryList = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/frontend_customer/order-history-list');
      setData(response.data);
      onComplete?.(response.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold text-gray-800">Order History List</h3>
      <button
        onClick={handleOrderHistoryList}
        disabled={loading}
        className="mt-3 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
      >
        {loading ? 'Processing...' : 'Execute'}
      </button>
      {error && <p className="mt-2 text-red-500 text-sm">{error}</p>}
      {data && <pre className="mt-2 p-2 bg-gray-50 rounded text-xs">{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
};

export default OrderHistoryList;
