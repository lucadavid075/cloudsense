import { useEffect, useState } from "react";
import { AlertCircle, HardDrive, Wifi, Server, Loader2, RefreshCw } from "lucide-react";
import { api, IdleResource, IdleResourceResult } from "../utils/api";

const TYPE_META: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  ebs_volume: { label: "Unattached EBS Volume", icon: HardDrive, color: "text-orange-400" },
  elastic_ip: { label: "Unattached Elastic IP", icon: Wifi, color: "text-yellow-400" },
  ec2_stopped: { label: "Stopped EC2 Instance", icon: Server, color: "text-blue-400" },
};

function ResourceCard({ resource }: { resource: IdleResource }) {
  const meta = TYPE_META[resource.resource_type] ?? {
    label: resource.resource_type,
    icon: AlertCircle,
    color: "text-gray-400",
  };
  const Icon = meta.icon;

  return (
    <div className="bg-[#0d1117] border border-gray-800 hover:border-gray-700 rounded-xl p-5 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 p-2 rounded-lg bg-gray-900">
            <Icon size={15} className={meta.color} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-200">{meta.label}</p>
            <p className="text-xs font-mono text-gray-500 mt-0.5">{resource.resource_id}</p>
          </div>
        </div>
        <div className="text-right">
          {resource.estimated_monthly_cost > 0 ? (
            <p className="text-sm font-mono text-red-400">
              ${resource.estimated_monthly_cost.toFixed(2)}/mo
            </p>
          ) : (
            <p className="text-xs text-gray-600">EBS storage cost</p>
          )}
          <p className="text-xs text-gray-600 mt-0.5">{resource.region}</p>
        </div>
      </div>

      {/* Details */}
      <div className="mt-3 pt-3 border-t border-gray-900 flex flex-wrap gap-x-4 gap-y-1">
        {Object.entries(resource.details).map(([k, v]) => {
          if (Array.isArray(v) || v === null || v === undefined) return null;
          return (
            <div key={k} className="text-xs">
              <span className="text-gray-600">{k.replace(/_/g, " ")}: </span>
              <span className="text-gray-400 font-mono">{String(v)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function Resources() {
  const [data, setData] = useState<IdleResourceResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    api
      .getIdleResources()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Idle Resources</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            AWS resources incurring cost without doing anything
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded-lg text-sm text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-40"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Rescan
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-48 gap-3 text-gray-500">
          <Loader2 size={18} className="animate-spin" />
          <span className="text-sm font-mono">Scanning AWS resources...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-950/30 border border-red-800/50 rounded-xl p-5 text-red-400 text-sm">
          <p className="font-semibold">Scan failed</p>
          <p className="mt-1 text-red-500">{error}</p>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Total Idle", value: data.summary.total_idle_resources, accent: "gray" },
              { label: "Unattached EBS", value: data.summary.unattached_ebs_volumes, accent: "orange" },
              { label: "Elastic IPs", value: data.summary.unattached_elastic_ips, accent: "yellow" },
              {
                label: "Monthly Waste",
                value: `$${data.summary.estimated_monthly_waste_usd.toFixed(2)}`,
                accent: "red",
              },
            ].map((s) => (
              <div
                key={s.label}
                className="bg-[#0d1117] border border-gray-800 rounded-xl p-4"
              >
                <p className="text-xs text-gray-500">{s.label}</p>
                <p className="text-2xl font-semibold text-white mt-1">{s.value}</p>
              </div>
            ))}
          </div>

          {/* Resource list */}
          {data.resources.length === 0 ? (
            <div className="bg-emerald-950/20 border border-emerald-800/30 rounded-xl p-8 text-center">
              <p className="text-emerald-400 font-medium">
                ✅ No idle resources found
              </p>
              <p className="text-gray-600 text-sm mt-1">
                Your account looks clean — no obvious waste detected.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {data.resources.map((r) => (
                <ResourceCard key={`${r.resource_type}-${r.resource_id}`} resource={r} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
