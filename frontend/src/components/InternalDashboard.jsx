import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Activity, Zap, BarChart2 } from 'lucide-react';

export default function InternalDashboard() {
  const [trainData, setTrainData] = useState([]);
  const [edaData, setEdaData] = useState(null);

  useEffect(() => {
    // 1. Đọc file training_log.csv tự động
    fetch('/training_log.csv')
      .then(res => res.text())
      .then(csvText => {
        const rows = csvText.trim().split('\n');
        // Bỏ qua dòng header (dòng 0), map dữ liệu từ dòng 1 trở đi
        const parsedData = rows.slice(1).map(row => {
          const cols = row.split(',');
          return {
            epoch: parseInt(cols[0]),
            phase: cols[1],
            train_loss: parseFloat(cols[2]),
            span_f1: parseFloat(cols[3]),
            sent_f1: parseFloat(cols[4]),
            composite: parseFloat(cols[6]),
            is_best: cols[8]?.trim() === 'best'
          };
        });
        setTrainData(parsedData);
      })
      .catch(err => console.error("Chưa có file training_log.csv trong folder public", err));

    // 2. Đọc file eda.json (Nếu bạn có)
    fetch('/eda.json')
      .then(res => res.json())
      .then(json => {
        setEdaData({
          aspects: json.aspect_distribution?.map(i => ({ name: i.aspect, count: i.count })) || [],
          sentiments: json.sentiment_distribution?.map(i => ({
            name: i.sentiment,
            value: i.count,
            color: i.sentiment === 'Positive' ? '#22c55e' : i.sentiment === 'Negative' ? '#ef4444' : '#f59e0b'
          })) || []
        });
      })
      .catch(err => console.log("Bỏ qua EDA vì chưa có file eda.json"));
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">📊 MLOps Dashboard</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Giám sát quá trình huấn luyện và dữ liệu hệ thống</p>
        </div>
        <div className="flex gap-3">
          <span className="px-3 py-1 bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 rounded-full text-sm font-medium">● Endpoint: InService</span>
        </div>
      </div>

      {/* --- PHẦN 1: KẾT QUẢ HUẤN LUYỆN MODEL (CSV) --- */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg"><Zap className="w-5 h-5 text-blue-600 dark:text-blue-400" /></div>
          <h2 className="text-xl font-bold dark:text-white">Model Training Progress (30 Epochs)</h2>
        </div>
        
        {trainData.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Biểu đồ Loss */}
            <div>
              <h3 className="text-sm font-bold text-center text-gray-500 mb-2">Training Loss giảm dần</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={trainData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                  <XAxis dataKey="epoch" tick={{fontSize: 12}} />
                  <YAxis yAxisId="left" tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{ borderRadius: '8px', backgroundColor: '#1f2937', color: '#fff' }} />
                  <Line yAxisId="left" type="monotone" dataKey="train_loss" stroke="#ef4444" strokeWidth={2} dot={false} name="Train Loss" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            {/* Biểu đồ F1-Score */}
            <div>
              <h3 className="text-sm font-bold text-center text-gray-500 mb-2">F1-Scores tăng dần</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={trainData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                  <XAxis dataKey="epoch" tick={{fontSize: 12}} />
                  <YAxis tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{ borderRadius: '8px', backgroundColor: '#1f2937', color: '#fff' }} />
                  <Legend />
                  <Line type="monotone" dataKey="span_f1" stroke="#3b82f6" strokeWidth={2} dot={false} name="Span F1" />
                  <Line type="monotone" dataKey="sent_f1" stroke="#10b981" strokeWidth={2} dot={false} name="Sentiment F1" />
                  <Line type="monotone" dataKey="composite" stroke="#f59e0b" strokeWidth={2} dot={false} name="Composite F1" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <p className="text-center text-gray-500 py-10">Đang tải dữ liệu huấn luyện từ CSV...</p>
        )}
      </div>

      {/* --- PHẦN 2: EDA DỮ LIỆU (JSON) --- */}
      {edaData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg"><BarChart2 className="w-5 h-5 text-blue-600 dark:text-blue-400" /></div>
              <h2 className="text-xl font-bold dark:text-white">Aspect Distribution</h2>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={edaData.aspects}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                <XAxis dataKey="name" tick={{fontSize: 11}} />
                <YAxis />
                <Tooltip contentStyle={{ borderRadius: '8px', backgroundColor: '#1f2937', color: '#fff' }} />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-6 border border-gray-100 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg"><Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" /></div>
              <h2 className="text-xl font-bold dark:text-white">Global Sentiment Balance</h2>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={edaData.sentiments} cx="50%" cy="50%" innerRadius={60} outerRadius={80} dataKey="value" label={({name}) => name}>
                  {edaData.sentiments.map((entry, index) => <Cell key={index} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', backgroundColor: '#1f2937', color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}