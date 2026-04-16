📝 [TEST #1] Input: áo rất xấu luôn thế mà giá còn hơi mắc nhưng nhân viên phục vụ rất tốt.
🌍 Global Sentiment: Pos 🟢
------------------------------------------------------------
📌 [Product   ] | Pos 🟢 | Target: 'áo'
   ∟ Audit: AI: Pos 🟢 (Uncertainty: 0.79) | Signals: NEG=1+GLB_POS ➡️ AI Retained
📌 [Price     ] | Pos 🟢 | Target: 'giá'
   ∟ Audit: AI: Pos 🟢 (Uncertainty: 0.79) | Signals: NEG=1+GLB_POS ➡️ AI Retained
📌 [Service   ] | Pos 🟢 | Target: 'nhân viên'
   ∟ Audit: AI: Pos 🟢 (Uncertainty: 0.79) | Signals: POS=1+GLB_POS ➡️ AI Retained

📝 [TEST #2] Input: App dùng hơi lag nhưng giá rẻ nên vẫn cho 5 sao, ship hơi lâu.
🌍 Global Sentiment: Pos 🟢
------------------------------------------------------------
📌 [App       ] | Pos 🟢 | Target: 'App'
   ∟ Audit: AI: Pos 🟢 (Uncertainty: 0.95) | Signals: GLB_POS ➡️ AI Retained
📌 [Price     ] | Pos 🟢 | Target: 'giá'
   ∟ Audit: AI: Pos 🟢 (Uncertainty: 0.95) | Signals: POS=1+GLB_POS ➡️ AI Retained
📌 [Ship      ] | Neg 🔴 | Target: 'ship'
   ∟ Audit: AI: Pos 🟢 (Uncertainty: 0.99) | Signals: NEG=1+GLB_POS ➡️ Neg 🔴

📝 [TEST #3] Input: Cái đồng hồ này đẹp tuyệt vời, nhân viên giao hàng rất nhanh.
🌍 Global Sentiment: Pos 🟢
------------------------------------------------------------
📌 [Service   ] | Pos 🟢 | Target: 'nhân viên'
   ∟ Audit: AI: Pos 🟢 (Uncertainty: 0.87) | Signals: POS=1+GLB_POS ➡️ AI Retained
📌 [Ship      ] | Pos 🟢 | Target: 'giao hàng'
   ∟ Audit: AI: Pos 🟢 (Uncertainty: 0.87) | Signals: POS=1+GLB_POS ➡️ AI Retained