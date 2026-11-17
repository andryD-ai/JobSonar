"""Prompt templates for Vietnam job market analysis and reporting."""

HR_SYSTEM_PROMPT = """Bạn là một Chuyên gia Phân tích Thị trường Lao động và Cố vấn Hướng nghiệp Công nghệ cấp cao tại Việt Nam (Senior IT & Tech Market Analyst).
Nhiệm vụ của bạn là tiếp nhận danh sách các tin tuyển dụng thực tế vừa được cào từ các nền tảng tuyển dụng hàng đầu (TopCV, ITviec, CareerViet, Facebook Fanpage...), phân tích sâu sắc các dữ liệu này và xuất ra một BÁO CÁO TOÀN DIỆN, THỰC CHIẾN và CỰC KỲ CHI TIẾT bằng tiếng Việt.

Yêu cầu về văn phong và phương pháp phân tích:
- Khách quan, dựa trên dữ liệu thực tế được cung cấp, không bịa đặt số liệu.
- Phân tích sâu sắc, đưa ra insight có giá trị cho cả ứng viên và nhà tuyển dụng.
- Định dạng Markdown chuẩn, chuyên nghiệp, sử dụng bảng biểu (table), bullet points và icon trực quan.
"""

def build_synthesis_prompt(keyword: str, total_jobs: int, jobs_summary: str) -> str:
    return f"""Dưới đây là dữ liệu thô của {total_jobs} tin tuyển dụng thực tế liên quan đến vị trí/từ khóa: **"{keyword}"** tại Việt Nam.

=== DỮ LIỆU CÁC TIN TUYỂN DỤNG ===
{jobs_summary}
=================================

Hãy tổng hợp và lập một **BÁO CÁO PHÂN TÍCH THỊ TRƯỜNG TUYỂN DỤNG MỚI NHẤT** cho vị trí **"{keyword}"**.
Báo cáo PHẢI bao gồm đầy đủ các mục lớn sau:

# 📊 BÁO CÁO THỊ TRƯỜNG TUYỂN DỤNG: {keyword.upper()}
*(Thời gian tổng hợp: Dữ liệu thực tế mới nhất)*

## 1. 📌 TỔNG QUAN THỊ TRƯỜNG
- Nhận định chung về nhu cầu tuyển dụng hiện nay đối với vị trí {keyword} tại Việt Nam.
- Tỷ lệ tin đăng giữa các nguồn (ITviec, TopCV, CareerViet, Facebook...).
- Mức độ sôi động của thị trường.

## 2. 💰 PHỔ LƯƠNG THỰC TẾ (SALARY BENCHMARK)
- Tạo bảng thống kê phổ lương theo cấp bậc (Intern/Fresher, Junior 1-2 năm, Middle 2-4 năm, Senior 4+ năm, Lead/Manager).
- Mức lương trung vị (median) phổ biến nhất trên thị trường.
- Phân tích mức lương giữa công ty Product vs Outsourcing, hoặc công ty trong nước vs doanh nghiệp FDI (nếu có dữ liệu).
- Tỷ lệ các tin tuyển dụng để mức lương "Thỏa thuận" vs công khai số tiền.

## 3. 🛠️ BẢN ĐỒ KỸ NĂNG & TECH STACK ĐƯỢC SĂN ĐÓN NHẤT
- **Kỹ năng bắt buộc (Must-have Core Skills)**: Top các ngôn ngữ, framework, database, công cụ xuất hiện với tần suất cao nhất.
- **Kỹ năng cộng điểm (Nice-to-have / Differentiators)**: Các công nghệ hiện đại giúp ứng viên nổi bật (Cloud, DevOps, AI tools, Architecture...).
- **Kỹ năng mềm & Ngoại ngữ**: Yêu cầu về tiếng Anh, làm việc nhóm, tư duy giải quyết vấn đề.

## 4. 📈 PHÂN BỐ CẤP BẬC & KINH NGHIỆM
- Cấp bậc nào đang được tuyển dụng nhiều nhất hiện nay?
- Cơ hội mở ra cho người mới bắt đầu (Fresher/Junior) có nhiều không?

## 5. 📍 ĐỊA ĐIỂM & HÌNH THỨC LÀM VIỆC
- Phân bố địa lý: TP. Hồ Chí Minh vs Hà Nội vs Đà Nẵng vs các tỉnh thành khác.
- Mô hình làm việc: Tỷ lệ Onsite vs Hybrid vs Remote 100%.

## 6. 🏢 TOP NHÀ TUYỂN DỤNG TIÊU BIỂU
- Liệt kê các công ty, tập đoàn đang tuyển dụng tích cực vị trí này trong tập dữ liệu.
- Các chế độ đãi ngộ, phúc lợi nổi bật thường thấy (thưởng, bảo hiểm, đào tạo, thiết bị làm việc...).

## 7. 🎯 LỜI KHUYÊN HÀNH ĐỘNG CHO ỨNG VIÊN
- **Tối ưu CV**: Ứng viên nên làm nổi bật từ khóa (keyword) và dự án nào trong hồ sơ để qua vòng lọc CV?
- **Lộ trình học tập/Nâng cấp**: Cần bổ sung kỹ năng gì để bắt kịp nhu cầu thị trường trong 6-12 tháng tới?
- **Chiến lược phỏng vấn**: Các chủ đề kỹ thuật và câu hỏi thường gặp mà ứng viên cần chuẩn bị kỹ.

Hãy phân tích thật chi tiết, có chiều sâu và trình bày đẹp mắt!
"""
