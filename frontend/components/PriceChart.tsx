import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface PricePoint {
  date: string;
  avg_price: number;
}

interface PriceChartProps {
  itemName: string;
  data: PricePoint[];
}

export default function PriceChart({ itemName, data }: PriceChartProps) {
  const chartData = {
    labels: data.map(d => d.date),
    datasets: [
      {
        label: 'Average Price (Yang)',
        data: data.map(d => d.avg_price),
        borderColor: 'rgb(59, 130, 246)', // Blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        tension: 0.3, // Smooth curves
        pointRadius: 4,
        pointBackgroundColor: 'rgb(96, 165, 250)',
      },
    ],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false, // Allow custom height
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#cbd5e1', // Slate-300
        }
      },
      title: {
        display: false,
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: '#1e293b',
        titleColor: '#f8fafc',
        bodyColor: '#f8fafc',
        borderColor: '#334155',
        borderWidth: 1,
        callbacks: {
            label: (context) => {
                let label = context.dataset.label || '';
                if (label) {
                    label += ': ';
                }
                if (context.parsed.y !== null) {
                     // Format large numbers (e.g. 1.5B)
                     const val = context.parsed.y;
                     if (val >= 100000000) {
                        label += (val / 100000000).toFixed(2) + ' Won';
                     } else {
                        label += val.toLocaleString() + ' Yang';
                     }
                }
                return label;
            }
        }
      },
    },
    scales: {
      x: {
        grid: {
          color: '#334155', // Slate-700
        },
        ticks: {
          color: '#94a3b8', // Slate-400
        }
      },
      y: {
        grid: {
          color: '#334155',
        },
        ticks: {
          color: '#94a3b8',
          callback: function(value) {
            // Simplify Y-axis labels
            const val = Number(value);
            if (val >= 100000000) return (val / 100000000).toFixed(1) + ' W';
            if (val >= 1000000) return (val / 1000000).toFixed(1) + ' M';
            return val;
          }
        }
      }
    },
    interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
    }
  };

  return (
    <div className="w-full h-full p-4 bg-slate-800 rounded-lg border border-slate-700">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-white">{itemName} - Price History</h3>
      </div>
      <div className="h-[300px]">
        {data.length > 0 ? (
           <Line options={options} data={chartData} />
        ) : (
            <div className="h-full flex items-center justify-center text-slate-500">
                No historical data available.
            </div>
        )}
      </div>
    </div>
  );
}
