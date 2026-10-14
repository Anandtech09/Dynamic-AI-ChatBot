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
  Brain,
  Sparkles,
  Cpu,
  ThumbsUp,
  ThumbsDown,
  Award,
  Zap,
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
  getLearningData,
} from '../services/api';
import type { AnalyticsOverview, ActivityData, RecentActivity, LearningStats } from '../types';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];
const SENTIMENT_COLORS: Record<string, string> = { positive: '#10b981', neutral: '#6b7280', negative: '#ef4444' };

export function AnalyticsDashboard() {
  const { setCurrentPage, toggleSidebar } = useStore();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [sentimentData, setSentimentData] = useState<any>(null);
  const [intentData, setIntentData] = useState<any>(null);
  const [activityData, setActivityData] = useState<ActivityData | null>(null);
  const [learningData, setLearningData] = useState<LearningStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, sent, intent, act, learn] = await Promise.all([
        getAnalyticsOverview(),
        getSentimentData(),
        getIntentData(),
        getActivityData(30),
        getLearningData().catch(() => ({ data: null })),
      ]);
      if (ov.data) setOverview(ov.data as AnalyticsOverview);
      if (sent.data) setSentimentData(sent.data);
      if (intent.data) setIntentData(intent.data);
      if (act.data) setActivityData(act.data as ActivityData);
      if (learn?.data) setLearningData(learn.data as LearningStats);
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
            <KPICard icon={<CheckCircle size={18} />} label="Success" value={overview.success_count} color="text-emerald-600" bg="bg-emerald-50 dark:bg-emerald-900/20 small" small />
            <KPICard icon={<XCircle size={18} />} label="Failures" value={overview.failure_count} color="text-red-600" bg="bg-red-50 dark:bg-red-900/20 small" small />
          </div>
        )}

        {/* Self-Learning AI Engine (RLHF Telemetry & learning_state.json) */}
        <SelfLearningSection data={learningData} />

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

function SelfLearningSection({ data }: { data: LearningStats | null }) {
  if (!data) return null;

  const adaptationPct = Math.min(100, Math.max(0, data.adaptation_score || 0));
  const avgReward = typeof data.average_reward === 'number' ? data.average_reward : 0;
  const cumReward = typeof data.cumulative_reward === 'number' ? data.cumulative_reward : 0;
  const interactions = data.interactions || 0;
  const totalFeedback = data.total_feedback || 0;
  const positive = data.positive_rewards || 0;
  const negative = data.negative_rewards || 0;

  // Intent policy weights
  const policyWeights = data.policy_weights || {};
  const standardIntents = ['rag_search', 'faq_query', 'technical', 'general_query', 'document_query'];
  const allPolicyEntries = Object.entries(policyWeights).length > 0
    ? Object.entries(policyWeights)
    : standardIntents.map((k) => [k, 1.0] as [string, number]);

  return (
    <div className="card p-5 sm:p-6 border border-indigo-500/20 bg-gradient-to-br from-indigo-950/20 via-surface-900/60 to-purple-950/20 shadow-xl dark:shadow-indigo-950/20">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-surface-200/60 dark:border-surface-800/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 shrink-0">
            <Brain size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-base sm:text-lg font-bold tracking-tight">Self-Learning AI Engine (RLHF Telemetry)</h2>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300">
                data/learning_state.json
              </span>
            </div>
            <p className="text-xs text-surface-500 dark:text-surface-400">
              Reinforcement Learning from Human Feedback & dynamic intent policy adaptation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Active Adaptation
          </span>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
        {/* Adaptation Score Card */}
        <div className="p-4 rounded-xl bg-white/60 dark:bg-surface-800/50 border border-surface-200/80 dark:border-surface-700/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-surface-500 dark:text-surface-400">Policy Adaptation Score</span>
            <Sparkles size={16} className="text-purple-500" />
          </div>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="text-2xl font-black text-indigo-600 dark:text-indigo-400">{adaptationPct.toFixed(1)}%</span>
            <span className="text-[11px] text-surface-500">
              {adaptationPct > 50 ? 'High Convergence' : adaptationPct > 15 ? 'Active Tuning' : 'Observation Mode'}
            </span>
          </div>
          <div className="w-full bg-surface-200 dark:bg-surface-700 h-2 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.max(5, adaptationPct)}%` }}
            />
          </div>
        </div>

        {/* Queries Learned Card */}
        <div className="p-4 rounded-xl bg-white/60 dark:bg-surface-800/50 border border-surface-200/80 dark:border-surface-700/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-surface-500 dark:text-surface-400">Queries Observed</span>
            <Cpu size={16} className="text-indigo-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black">{interactions}</span>
            <span className="text-[11px] text-surface-500">interactions</span>
          </div>
          <p className="text-[11px] text-surface-500 dark:text-surface-400 mt-2">
            User queries observed & tracked for model adaptation
          </p>
        </div>

        {/* Human Feedback Card */}
        <div className="p-4 rounded-xl bg-white/60 dark:bg-surface-800/50 border border-surface-200/80 dark:border-surface-700/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-surface-500 dark:text-surface-400">Human Feedback Signals</span>
            <div className="flex items-center gap-1 text-emerald-500">
              <ThumbsUp size={14} />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black">{totalFeedback}</span>
            <span className="text-[11px] text-surface-500">ratings</span>
          </div>
          <div className="flex items-center gap-3 mt-2 text-xs font-medium">
            <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
              <ThumbsUp size={12} /> {positive} positive
            </span>
            <span className="inline-flex items-center gap-1 text-rose-600 dark:text-rose-400">
              <ThumbsDown size={12} /> {negative} negative
            </span>
          </div>
        </div>

        {/* Mean Reward Card */}
        <div className="p-4 rounded-xl bg-white/60 dark:bg-surface-800/50 border border-surface-200/80 dark:border-surface-700/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-surface-500 dark:text-surface-400">Mean Reward (R ∈ [-1, +1])</span>
            <Award size={16} className="text-emerald-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-black ${avgReward > 0 ? 'text-emerald-600 dark:text-emerald-400' : avgReward < 0 ? 'text-rose-600' : 'text-surface-600'}`}>
              {avgReward > 0 ? `+${avgReward.toFixed(2)}` : avgReward.toFixed(2)}
            </span>
            <span className="text-[11px] text-surface-500">normalized</span>
          </div>
          <p className="text-[11px] text-surface-500 dark:text-surface-400 mt-2">
            Cumulative reinforcement score: <span className="font-semibold text-surface-700 dark:text-surface-300">{cumReward > 0 ? `+${cumReward.toFixed(2)}` : cumReward.toFixed(2)}</span>
          </p>
        </div>
      </div>

      {/* Detail Panels: Policy Multipliers & Top Rewarded Intents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* Policy Multipliers Panel */}
        <div className="p-4 rounded-xl bg-surface-50/50 dark:bg-surface-800/30 border border-surface-200/70 dark:border-surface-800">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Zap size={15} className="text-amber-500" />
                Intent Policy Multipliers (W<sub>intent</sub>)
              </h3>
              <p className="text-[11px] text-surface-500">
                Reinforced weights range between 0.70× (penalized) and 1.30× (rewarded)
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-300">
              1.00× = Baseline
            </span>
          </div>

          <div className="space-y-3 mt-3">
            {allPolicyEntries.map(([intent, weight]) => {
              const diff = weight - 1.0;
              const isBoosted = diff > 0.001;
              const isPenalized = diff < -0.001;
              const barWidth = Math.min(100, Math.max(10, ((weight - 0.7) / 0.6) * 100));

              return (
                <div key={intent} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-surface-700 dark:text-surface-300 font-mono text-[11px]">
                      {intent}
                    </span>
                    <span className={`font-semibold font-mono text-[11px] ${
                      isBoosted
                        ? 'text-emerald-600 dark:text-emerald-400'
                        : isPenalized
                        ? 'text-rose-600 dark:text-rose-400'
                        : 'text-surface-500'
                    }`}>
                      {weight.toFixed(2)}× {isBoosted ? '(Boosted)' : isPenalized ? '(Penalized)' : '(Balanced)'}
                    </span>
                  </div>
                  <div className="w-full bg-surface-200 dark:bg-surface-700/60 h-2 rounded-full overflow-hidden relative">
                    <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-surface-400/50 z-10" />
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isBoosted
                          ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                          : isPenalized
                          ? 'bg-gradient-to-r from-rose-500 to-amber-500'
                          : 'bg-primary-500'
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-4 p-2.5 rounded-lg bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200/60 dark:border-indigo-800/50 text-[11px] text-indigo-800 dark:text-indigo-300 leading-relaxed">
            💡 <strong>How Policy Weights Work:</strong> When you rate assistant answers in the chat using thumbs up/down,
            the self-learning module rewards or penalizes the underlying intent policy in <code>data/learning_state.json</code>, automatically adapting response selection over time.
          </div>
        </div>

        {/* Top Rewarded Intents / Feedback History Panel */}
        <div className="p-4 rounded-xl bg-surface-50/50 dark:bg-surface-800/30 border border-surface-200/70 dark:border-surface-800 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold flex items-center gap-2 mb-1">
              <Award size={15} className="text-indigo-500" />
              Reinforcement Rankings & Feedback Events
            </h3>
            <p className="text-[11px] text-surface-500 mb-3">
              Most rewarded intent categories and recent human reinforcement logs
            </p>

            {data.top_rewarded_intents && data.top_rewarded_intents.length > 0 ? (
              <div className="space-y-2">
                {data.top_rewarded_intents.map((item, idx) => (
                  <div
                    key={item.intent}
                    className="flex items-center justify-between p-2 rounded-lg bg-white/70 dark:bg-surface-800/60 border border-surface-200/60 dark:border-surface-700/40 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 flex items-center justify-center font-bold text-[10px]">
                        #{idx + 1}
                      </span>
                      <span className="font-medium font-mono text-surface-800 dark:text-surface-200">{item.intent}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[11px] text-surface-500">{item.count} feedbacks</span>
                      <span className={`px-2 py-0.5 rounded-md font-mono font-bold text-[11px] ${
                        item.avg_reward > 0
                          ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300'
                          : 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300'
                      }`}>
                        {item.avg_reward > 0 ? `+${item.avg_reward.toFixed(2)}` : item.avg_reward.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center text-surface-400">
                <Sparkles size={24} className="mx-auto mb-2 opacity-40 text-indigo-500" />
                <p className="text-xs font-medium text-surface-600 dark:text-surface-300">Ready for Human Feedback</p>
                <p className="text-[11px] text-surface-500 max-w-xs mx-auto mt-1">
                  Interact with the bot in Chat and rate answers with thumbs up/down. The RLHF telemetry here will immediately visualize the live rewards.
                </p>
              </div>
            )}
          </div>

          {data.rewards_history && data.rewards_history.length > 0 && (
            <div className="mt-4 pt-3 border-t border-surface-200 dark:border-surface-700/60">
              <span className="text-[11px] font-semibold text-surface-500 block mb-2">Recent Feedback Log</span>
              <div className="space-y-1.5 max-h-32 overflow-y-auto">
                {data.rewards_history.slice(0, 4).map((r, i) => (
                  <div key={i} className="flex items-center justify-between text-[11px] p-1.5 rounded-lg bg-surface-100/70 dark:bg-surface-800/40">
                    <span className="font-mono text-surface-600 dark:text-surface-300">{r.intent}</span>
                    <span className={`font-bold font-mono ${r.reward > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-500'}`}>
                      {r.reward > 0 ? `+${r.reward.toFixed(1)}` : r.reward.toFixed(1)} ({r.rating}★)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
