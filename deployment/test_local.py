from inference import model_fn, predict_fn

# Giả lập SageMaker load model
print("Loading model...")
model_dict = model_fn("model") # "." nghĩa là tìm file .pt ở thư mục hiện tại

# Chạy thử một câu test
test_input = "Điện thoại đẹp nhưng giao hàng lâu"
print(f"Testing with: {test_input}")
prediction = predict_fn(test_input, model_dict)

print("\nResult:")
print(prediction)