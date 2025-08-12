# ReadZone - Website Bán Sách và Đọc Sách Trực Tuyến
**Tác giả:** Trương Tiến Đạt, Trần Ngọc Duy  
*[Báo cáo chi tiết](https://drive.google.com/file/d/1FvzqHbn3-YIdZxqVNon3drQObalNwA-G/view?usp=sharing)*

---
## 1. Giới thiệu
**ReadZone** là hệ thống bán sách và đọc sách trực tuyến được xây dựng nhằm cung cấp một nền tảng tích hợp đầy đủ chức năng cho cả khách hàng và người bán hàng, với luồng xử lý chặt chẽ từ đăng nhập đến thanh toán và quản lý. 
### 🔹 Chức năng dành cho khách hàng
- **Đăng ký/Đăng nhập** và lưu thông tin cá nhân.
- **Tìm kiếm sách** theo thể loại, tác giả, giá bán.
- **Xem chi tiết sách** (mô tả, đánh giá, bình luận, sách liên quan).
- **Thêm vào giỏ hàng** và thanh toán qua **Momo QR**.
- **Theo dõi trạng thái đơn hàng**.
- **Đọc sách trực tuyến** (gói miễn phí hoặc premium).
- **Chatbox AI** gợi ý sách phù hợp.

### 🔹 Chức năng dành cho người bán 
- **Quản lý sách**: thêm/sửa/xóa thể loại, tác giả, sách.
- **Quản lý kho**: nhập hàng, xuất phiếu, theo dõi tồn kho.
- **Quản lý đơn hàng** & xác nhận thanh toán.
- **Cấu hình gói đọc sách** miễn phí và premium.
- **Thêm nội dung đọc online** từ file Word hoặc nhập thủ công.
- **Thống kê doanh thu & báo cáo đánh giá**.
- **Quản lý & phân quyền nhân viên**.


## 2. Công nghệ sử dụng
- **Frontend:** HTML, CSS, Bootstrap  
- **Backend:** Python (Flask)  
- **Database:** MySQL  
- **Thanh toán:** Momo Payment API  
- **AI Chatbox:** Gợi ý sách tự động  
- **IDE:** PyCharm  


## 3. Cài đặt 

### Bước 1: Clone repo
```bash
git clone https://github.com/truongtiendat19/btl/branches
cd btl
```
### Bước 2: Cài đặt thư viện
```bash
pip install -r requirements.txt
```
