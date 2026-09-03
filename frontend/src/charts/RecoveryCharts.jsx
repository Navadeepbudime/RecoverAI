import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts'

const palette = ['#2a9d8f', '#e9c46a', '#e76f51', '#457b9d', '#14213d', '#8d99ae']

export function Donut({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data || []} dataKey="value" nameKey="name" innerRadius={64} outerRadius={100} paddingAngle={3}>
          {(data || []).map((_, index) => <Cell key={index} fill={palette[index % palette.length]} />)}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function Bars({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data || []}>
        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
        <YAxis allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="value" fill="#2a9d8f" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
