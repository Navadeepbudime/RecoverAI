import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Legend,
} from 'recharts'

const palette = ['#2a9d8f', '#e9c46a', '#e76f51', '#457b9d', '#14213d', '#8d99ae']

export function Donut({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data || []} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95} paddingAngle={3}>
          {(data || []).map((_, index) => (
            <Cell key={index} fill={palette[index % palette.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function Bars({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
        <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" interval={0} />
        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="value" name="Incidents" fill="#2a9d8f" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function ComparativeCategoryChart({ data }) {
  // data is [{ category, baseline, recoverai, total_at_risk }]
  const formatted = (data || []).map((d) => ({
    category: d.category.replace('Checkout Abandonment', 'Abandonment'),
    'Naive Retry': Math.round(d.baseline || 0),
    RecoverAI: Math.round(d.recoverai || 0),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={formatted} margin={{ top: 15, right: 20, left: 10, bottom: 25 }}>
        <XAxis dataKey="category" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" interval={0} />
        <YAxis
          tick={{ fontSize: 11 }}
          tickFormatter={(v) => `₹${v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v}`}
        />
        <Tooltip formatter={(val) => `₹${Number(val).toLocaleString('en-IN')}`} />
        <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '15px' }} />
        <Bar dataKey="Naive Retry" fill="#94a3b8" radius={[3, 3, 0, 0]} />
        <Bar dataKey="RecoverAI" fill="#2a9d8f" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
