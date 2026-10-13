import React, { useEffect, useState } from 'react';
import {
  MessageSquare,
  MessagesSquare,
  Clock,
  TrendingUp,
  TrendingDown,
  SmilePlus,
  Frown,
  Meh,
  Activity,
  CheckCircle,
  XCircle,
  Star,
  ArrowLeft,
  Menu,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area,
} from 'recharts';
import { useStore } from '../store/useStore';
import {
  getAnalyticsOverview,
  getSentimentData,
  getIntentData,
  getActivityData,
} from '../services/api';
import type { AnalyticsOverview, ActivityData, RecentActivity } from '../types';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];
const SENTIMENT_COLORS: Record<string, string> = { positive: '#10b981', neutral: '#6b7280', negative: '#ef4444' };

export function AnalyticsDashboard() {
  const { setCurrentPage, toggleSidebar } = useStore();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [sentimentData, setSentimentData] = useState<any>(null);
  const [intentData, setIntentData] = useState<any>(null);
  const [activityData, setActivityData] = useState<ActivityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, sent, intent, act] = await Promise.all([
        getAnalyticsOverview(),
        getSentimentData(),
        getIntentData(),
        getActivityData(30),
      ]);
      if (ov.data) setOverview(ov.data as AnalyticsOverview);
      if (sent.data) setSentimentData(sent.data);
      if (intent.data) setIntentData(intent.data);
      if (act.data) setActivityData(act.data as ActivityData);
    } catch (e: any) {
      setError(e.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-3 animate-pulse">
          <Activity size={40} className="text-primary-500" />
          <p className="text-surface-500">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="card p-8 text-center max-w-sm">
          <XCircle size={40} className="text-red-500 mx-auto mb-3" />
          <p className="text-surface-600 dark:text-surface-400 mb-4">{error}</p>
          <button onClick={loadData} className="btn-primary">Retry</button>
        </div>
      </div>
    );
  }

  const sentimentPieData = sentimentData?.distribution?.map((s: any) => ({
    name: s.label || 'unknown',
    value: s.count,
    color: SENTIMENT_COLORS[s.label] || '#6b7280',
  })) || [];

  const intentBarData = intentData?.intents?.slice(0, 10) || [];

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/80 dark:bg-surface-900/80 backdrop-blur-sm border-b border-surface-200 dark:border-surface-800 px-4 sm:px-6 py-3.5 sm:py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Mobile menu toggle */}
            <button
              onClick={toggleSidebar}
              className="btn-ghost p-1.5 lg:hidden text-surface-600 dark:text-surface-300"
              aria-label="Open navigation menu"
            >
              <Menu size={20} />
            </button>

            <div>
              <h1 className="text-base sm:text-xl font-semibold leading-tight">Analytics Dashboard</h1>
              <p className="text-xs sm:text-sm text-surface-500 hidden sm:block">Insights from your conversations</p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        {overview && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPICard icon={<MessageSquare size={20} />} label="Conversations" value={overview.total_conversations} color="text-primary-600" bg="bg-primary-50 dark:bg-primary-900/20" />
            <KPICard icon={<MessagesSquare size={20} />} label="Messages" value={overview.total_messages} color="text-emerald-600" bg="bg-emerald-50 dark:bg-emerald-900/20" />
            <KPICard icon={<Clock size={20} />} label="Avg Response" value={`${Math.round(overview.avg_response_time_ms)}ms`} color="text-amber-600" bg="bg-amber-50 dark:bg-amber-900/20" />
            <KPICard icon={<Star size={20} />} label="Avg Rating" value={overview.avg_feedback_rating > 0 ? overview.avg_feedback_rating.toFixed(1) : '—'} color="text-violet-600" bg="bg-violet-50 dark:bg-violet-900/20" />
          </div>
        )}

        {overview && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <KPICard icon={<SmilePlus size={18} />} label="Positive" value={`${overview.positive_pct}%`} color="text-emerald-600" bg="bg-emerald-50 dark:bg-emerald-900/20" small />
            <KPICard icon={<Meh size={18} />} label="Neutral" value={`${overview.neutral_pct}%`} color="text-surface-500" bg="bg-surface-100 dark:bg-surface-800" small />
            <KPICard icon={<Frown size={18} />} label="Negative" value={`${overview.negative_pct}%`} color="text-red-600" bg="bg-red-50 dark:bg-red-900/20" small />
            <KPICard icon={<CheckCircle size={18} />} label="Success" value={overview.success_count} color="text-emerald-600" bg="bg-emerald-50 dark:bg-emerald-900/20" small />
            <KPICard icon={<XCircle size={18} />} label="Failures" value={overview.failure_count} color="text-red-600" bg="bg-red-50 dark:bg-red-900/20" small />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-5">
            <h3 className="font-semibold text-sm mb-4">Messages Over Time</h3>
            {activityData?.messages_over_time?.length ? (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={activityData.messages_over_time}>
                  <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-surface-200 dark:text-surface-700" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : <EmptyChart />}
          </div>

          <div className="card p-5">
            <h3 className="font-semibold text-sm mb-4">Sentiment Distribution</h3>
            {sentimentPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={sentimentPieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={4} dataKey="value">
                    {sentimentPieData.map((entry: any, i: number) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : <EmptyChart />}
            {sentimentPieData.length > 0 && (
              <div className="flex justify-center gap-4 mt-2">
                {sentimentPieData.map((entry: any) => (
                  <div key={entry.name} className="flex items-center gap-1.5 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                    {entry.name} ({entry.value})
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-5">
            <h3 className="font-semibold text-sm mb-4">Top Detected Intents</h3>
            {intentBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={intentBarData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-surface-200 dark:text-surface-700" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="intent" tick={{ fontSize: 11 }} width={120} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyChart />}
          </div>

          <div className="card p-5">
            <h3 className="font-semibold text-sm mb-4">Response Latency (ms)</h3>
            {activityData?.response_latency?.length ? (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={activityData.response_latency}>
                  <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-surface-200 dark:text-surface-700" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="avg_ms" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : <EmptyChart />}
          </div>
        </div>

        <div className="card p-5">
          <h3 className="font-semibold text-sm mb-4">Recent Activity</h3>
          {activityData?.recent_activity?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-surface-500 dark:text-surface-400 text-xs uppercase tracking-wider">
                    <th className="px-3 py-2">Time</th>
                    <th className="px-3 py-2">Message</th>
                    <th className="px-3 py-2">Intent</th>
                    <th className="px-3 py-2">Sentiment</th>
                    <th className="px-3 py-2">Latency</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100 dark:divide-surface-800">
                  {activityData.recent_activity.map((item: RecentActivity, i: number) => (
                    <tr key={i} className="hover:bg-surface-50 dark:hover:bg-surface-800/50">
                      <td className="px-3 py-2.5 text-xs text-surface-500 whitespace-nowrap">
                        {item.timestamp ? new Date(item.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                      </td>
                      <td className="px-3 py-2.5 max-w-[200px] truncate">{item.message_preview}</td>
                      <td className="px-3 py-2.5"><span className="badge badge-neutral">{item.intent || '—'}</span></td>
                      <td className="px-3 py-2.5">
                        <span className={`badge ${item.sentiment === 'positive' ? 'badge-positive' : item.sentiment === 'negative' ? 'badge-negative' : 'badge-neutral'}`}>
                          {item.sentiment || '—'}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-xs">{item.response_time_ms ? `${item.response_time_ms}ms` : '—'}</td>
                      <td className="px-3 py-2.5">
                        {item.is_error ? <XCircle size={14} className="text-red-500" /> : <CheckCircle size={14} className="text-emerald-500" />}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-surface-400">
              <Activity size={32} className="mx-auto mb-2 opacity-50" />
              <p className="text-sm">No activity recorded yet. Start chatting to see data here.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function KPICard({ icon, label, value, color, bg, small }: { icon: React.ReactNode; label: string; value: string | number; color: string; bg: string; small?: boolean }) {
  return (
    <div className={`card ${small ? 'p-3' : 'p-4'} flex items-center gap-3`}>
      <div className={`${small ? 'p-2' : 'p-2.5'} rounded-xl ${bg} ${color}`}>{icon}</div>
      <div>
        <p className={`${small ? 'text-lg' : 'text-xl'} font-bold`}>{value}</p>
        <p className="text-xs text-surface-500">{label}</p>
      </div>
    </div>
  );
}

function EmptyChart() {
  return (
    <div className="flex items-center justify-center h-[250px] text-surface-400">
      <div className="text-center">
        <Activity size={24} className="mx-auto mb-2 opacity-40" />
        <p className="text-xs">No data yet</p>
      </div>
    </div>
  );
}
