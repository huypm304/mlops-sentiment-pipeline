import React from 'react';
import { useState } from 'react';
import { Zap, MessageSquare } from 'lucide-react';

export default function CustomerPortal() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Lỗi kết nối Backend:", error);
      alert("Không thể kết nối tới Backend! Hãy chắc chắn uvicorn đang chạy.");
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white mb-4">
          Customer <span className="text-blue-600">Feedback</span> Analysis
        </h1>
        <p className="text-gray-500 dark:text-gray-400">Trải nghiệm sức mạnh của ABSA ngay lập tức.</p>
      </div>

      {/* Input Section */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 border border-gray-100 dark:border-gray-700">
        <textarea
          className="w-full h-32 p-4 rounded-xl border border-gray-200 dark:border-gray-600 dark:bg-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
          placeholder="Nhập đánh giá sản phẩm tại đây..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-50"
        >
          {loading ? "Đang phân tích..." : <><Zap size={18} /> Phân tích ngay</>}
        </button>
      </div>

      {/* Result Section */}
      {result && (
        <div className="mt-8 space-y-4">
          <h3 className="text-xl font-bold dark:text-white flex items-center gap-2">
            <MessageSquare className="text-blue-500" /> Kết quả phân tích:
          </h3>

          {/* Global Sentiment Card */}
          <div className="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-2xl border border-blue-200 dark:border-blue-800 flex items-center justify-between shadow-sm">
            <div>
              <p className="text-sm text-blue-600 dark:text-blue-400 font-medium">Đánh giá tổng thể (Global):</p>
              <h4 className="text-2xl font-black dark:text-white uppercase tracking-wider">
                {result.global_sentiment || "Neutral"}
              </h4>
            </div>
            <div className="text-4xl">
              {result.global_sentiment === 'Positive' ? '😊' : result.global_sentiment === 'Negative' ? '😞' : '😐'}
            </div>
          </div>

          {/* Aspects Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {result.aspects?.map((item, idx) => (
              <div key={idx} className="bg-white dark:bg-gray-800 p-4 rounded-xl border-l-4 border-blue-500 shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-gray-700 dark:text-gray-200 uppercase">{item.aspect}</span>
                  <span className={`px-2 py-1 rounded-md text-xs font-bold ${
                    item.sentiment === 'Positive' ? 'bg-green-100 text-green-700' : 
                    item.sentiment === 'Negative' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {item.sentiment}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-2 italic">Target: "{item.target}"</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}