import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { TrendingUp, DollarSign, AlertTriangle, Zap } from "lucide-react";
import { api, DailyCost, ServiceTotal, Anomaly, ForecastResult } from "../utils/api";

const SERVICE_COLORS = [
  "#4f72e8", "#7c3aed", "#059669", "#d97706",
  "#dc2626", "#0891b2", "#7c2d12", "#4338ca",
];

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  accent = "blue",
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  accent?: string;
}) {
  const colors: Record<string, string> = {
    blue: "text-blue-400 bg-blue-500/10",
    green: "text-emerald-400 bg-emerald-500/10",
    yellow: "text-yellow-400 bg-yellow-500/10",
    red: "text-red-400 bg-red-500/10",
  };

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-semibold text-white mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-600 mt-1">{sub}</p>}
        </div>
        <div className={`p-2 rounded-lg ${colors[accent]}`}>
          <Icon size={18} />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [daily, setDaily] = useState<DailyCost[]>([]);
  const [services, setServices] = useState<ServiceTotal[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.getDailyCosts(30),
      api.getCostsByService(30),
      api.getAnomalies(30),
      api.getForecast(30),
    ])
      .then(([dailyRes, serviceRes, anomalyRes, forecastRes]) => {
        setDaily(dailyRes.data);
        setTotal(dailyRes.total);
        setServices(serviceRes.by_service.slice(0, 8));
        setAnomalies(anomalyRes.anomalies);
        setForecast(forecastRes);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const avg = daily.length ? total / daily.length : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500 font-mono text-sm animate-pulse">
          Fetching AWS cost data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-950/30 border border-red-800/50 rounded-xl p-6 text-red-400">
        <p className="font-semibold">Failed to load cost data</p>
        <p className="text-sm mt-1 text-red-500">{error}</p>
        <p className="text-xs mt-2 text-red-600">
          Check your AWS credentials in .env and ensure Cost Explorer is enabled.
        </p>
      </div>
    );
  }

  const formattedDaily = daily.map((d) => ({
    ...d,
    date: d.date.slice(5), // MM-DD
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-white">Cost Overview</h1>
        <p className="text-sm text-gray-500 mt-0.5">Last 30 days · AWS</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Total Spend (30d)"
          value={`$${total.toFixed(2)}`}
          sub="unblended cost"
          icon={DollarSign}
          accent="blue"
        />
        <StatCard
          label="Daily Average"
          value={`$${avg.toFixed(2)}`}
          sub="per day"
          icon={TrendingUp}
          accent="green"
        />
        <StatCard
          label="Cost Anomalies"
          value={`${anomalies.length}`}
          sub="days above threshold"
          icon={AlertTriangle}
          accent={anomalies.length > 0 ? "yellow" : "green"}
        />
        <StatCard
          label="30-Day Forecast"
          value={forecast?.error ? "N/A" : `$${forecast?.mean_value.toFixed(2) ?? "—"}`}
          sub={forecast?.error ? "insufficient data" : "projected"}
          icon={Zap}
          accent="blue"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-3 gap-4">
        {/* Daily spend chart */}
        <div className="col-span-2 bg-[#0d1117] border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-medium text-gray-300 mb-4">Daily Spend</h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={formattedDaily}>
              <defs>
                <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4f72e8" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#4f72e8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="date"
                tick={{ fill: "#6b7280", fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                interval={6}
              />
              <YAxis
                tick={{ fill: "#6b7280", fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#111827",
                  border: "1px solid #374151",
                  borderRadius: 8,
                  color: "#e5e7eb",
                }}
                formatter={(v: number) => [`$${v.toFixed(4)}`, "Cost"]}
              />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="#4f72e8"
                strokeWidth={2}
                fill="url(#costGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Service pie chart */}
        <div className="bg-[#0d1117] border border-gray-800 rounded-xl p-5">
          <h2 className="text-sm font-medium text-gray-300 mb-4">By Service</h2>
          {services.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={services}
                  dataKey="total"
                  nameKey="service"
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  label={false}
                >
                  {services.map((_, i) => (
                    <Cell key={i} fill={SERVICE_COLORS[i % SERVICE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#111827",
                    border: "1px solid #374151",
                    borderRadius: 8,
                    color: "#e5e7eb",
                    fontSize: 12,
                  }}
                  formatter={(v: number) => [`$${v.toFixed(2)}`, ""]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-600 text-sm">No service data</p>
          )}
        </div>
      </div>

      {/* Top services table */}
      <div className="bg-[#0d1117] border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h2 className="text-sm font-medium text-gray-300">Top Services by Cost</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-5 py-3 text-gray-600 font-medium">#</th>
              <th className="text-left px-5 py-3 text-gray-600 font-medium">Service</th>
              <th className="text-right px-5 py-3 text-gray-600 font-medium">30d Cost</th>
              <th className="text-right px-5 py-3 text-gray-600 font-medium">% of Total</th>
            </tr>
          </thead>
          <tbody>
            {services.map((svc, i) => (
              <tr key={svc.service} className="border-b border-gray-900 hover:bg-white/2">
                <td className="px-5 py-3 text-gray-700 font-mono">{i + 1}</td>
                <td className="px-5 py-3 text-gray-300">{svc.service}</td>
                <td className="px-5 py-3 text-right font-mono text-white">
                  ${svc.total.toFixed(2)}
                </td>
                <td className="px-5 py-3 text-right text-gray-500">
                  {total > 0 ? ((svc.total / total) * 100).toFixed(1) : 0}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Anomalies */}
      {anomalies.length > 0 && (
        <div className="bg-yellow-950/20 border border-yellow-800/30 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={16} className="text-yellow-500" />
            <h2 className="text-sm font-medium text-yellow-400">
              Spend Anomalies Detected
            </h2>
          </div>
          <div className="space-y-2">
            {anomalies.map((a) => (
              <div
                key={a.date}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-gray-400 font-mono">{a.date}</span>
                <span className="text-yellow-400 font-mono">
                  ${a.amount.toFixed(2)}
                  <span className="text-yellow-700 ml-2">
                    ({a.multiplier}× avg)
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
