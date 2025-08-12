const chatBody = document.querySelector(".chat-body");
const messageInput = document.querySelector(".message-input");
const sendMessageButton = document.querySelector("#send-message");
const fileInput = document.querySelector("#file-input");
const fileUploadWrapper = document.querySelector(".file-upload-wrapper");
const fileCancelButton = document.querySelector("#file-cancel");
const chatbotToggler = document.querySelector("#chatbot-toggler");
const closeChatbot = document.querySelector("#close-chatbot");

// API setup
const API_KEY = "AIzaSyAgnwuotspbwJQrVgtshyvyU_xgjbygJXg";
const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${API_KEY}`;

const userData = {
    message: null,
    file: {
        data: null,
        mime_type: null
    }
};

// Lịch sử chat
let chatHistory = [
    {
        role: "model",
        parts: [{
            text: `Tôi là trợ lý bán hàng của cửa hàng sách trực tuyến ReadZone.
- Giới thiệu sách theo nhu cầu.
- Trả lời về giá, tác giả, thể loại, nội dung tóm tắt.
- Đề xuất sách theo sở thích khách hàng.
- Hướng dẫn thêm vào giỏ & thanh toán.
Luôn trả lời thân thiện, ngắn gọn, dễ hiểu.`
        }]
    }
];

// Load lịch sử từ localStorage
const savedHistory = localStorage.getItem("chatHistory");
if (savedHistory) {
    try {
        const parsed = JSON.parse(savedHistory);
        if (Array.isArray(parsed)) chatHistory = parsed;
    } catch (e) {
        console.error("Không thể đọc chatHistory từ localStorage");
    }
}

// Lấy dữ liệu sách từ API Flask và đưa vào chatHistory
fetch("/api/chatbot/books")
    .then(res => res.json())
    .then(books => {
        if (books.length) {
            const bookListText = books.map(b =>
                `${b.name} - Tác giả: ${b.author || "Không rõ"}, Giá: ${b.price} VNĐ, Thể loại: ${b.category || "Không rõ"}.`
            ).join("\n");
            chatHistory.push({
                role: "model",
                parts: [{
                    text: `Dữ liệu sách hiện tại:\n${bookListText}\nHãy dùng thông tin này để tư vấn chính xác.`
                }]
            });
            saveChatHistory();
        }
    })
    .catch(err => console.error("Lỗi tải sách:", err));

// Lưu lịch sử chat
function saveChatHistory() {
    localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
}

const initialInputHeight = messageInput.scrollHeight;

// Tạo phần tử tin nhắn
const createMessageElement = (content, ...classes) => {
    const div = document.createElement("div");
    div.classList.add("message", ...classes);
    div.innerHTML = content;
    return div;
};

// Gửi yêu cầu tới API Gemini
const generateBotResponse = async (incomingMessageDiv) => {
    const messageElement = incomingMessageDiv.querySelector(".message-text");

    chatHistory.push({
        role: "user",
        parts: [{ text: userData.message }, ...(userData.file.data ? [{ inline_data: userData.file }] : [])],
    });

    const requestOptions = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contents: chatHistory })
    }

    try {
        const response = await fetch(API_URL, requestOptions);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error.message);

        const apiResponseText = data.candidates[0].content.parts[0].text
            .replace(/\*\*(.*?)\*\*/g, "$1")
            .trim();

        messageElement.innerText = apiResponseText;
        chatHistory.push({
            role: "model",
            parts: [{ text: apiResponseText }]
        });
        saveChatHistory();
    } catch (error) {
        messageElement.innerText = error.message;
        messageElement.style.color = "#ff0000";
    } finally {
        userData.file = {};
        incomingMessageDiv.classList.remove("thinking");
        chatBody.scrollTo({ behavior: "smooth", top: chatBody.scrollHeight });
    }
};

// Xử lý gửi tin nhắn
const handleOutgoingMessage = (e) => {
    e.preventDefault();
    userData.message = messageInput.value.trim();
    if (!userData.message) return;

    messageInput.value = "";
    fileUploadWrapper.classList.remove("file-uploaded");
    messageInput.dispatchEvent(new Event("input"));

    const messageContent = `<div class="message-text"></div>
        ${userData.file.data ? `<img src="data:${userData.file.mime_type};base64,${userData.file.data}" class="attachment" />` : ""}`;

    const outgoingMessageDiv = createMessageElement(messageContent, "user-message");
    outgoingMessageDiv.querySelector(".message-text").innerText = userData.message;
    chatBody.appendChild(outgoingMessageDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    setTimeout(() => {
        const messageContent = `<svg class="bot-avatar" xmlns="http://www.w3.org/2000/svg" width="50" height="50">
            <path d="M738.3 287.6H285.7c-59 0-106.8 47.8-106.8 106.8v303.1c0 59 47.8 106.8 106.8 106.8h81.5v111.1c0 .7.8 1.1 1.4.7l166.9-110.6 41.8-.8h117.4l43.6-.4c59 0 106.8-47.8 106.8-106.8V394.5c0-59-47.8-106.9-106.8-106.9z"></path>
        </svg>
        <div class="message-text">
            <div class="thinking-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>`;

        const incomingMessageDiv = createMessageElement(messageContent, "bot-message", "thinking");
        chatBody.appendChild(incomingMessageDiv);
        chatBody.scrollTo({ behavior: "smooth", top: chatBody.scrollHeight });
        generateBotResponse(incomingMessageDiv);
    }, 500);
};

// Sự kiện Enter
messageInput.addEventListener("keydown", (e) => {
    const userMessage = e.target.value.trim();
    if (e.key === "Enter" && userMessage && !e.shiftKey) {
        handleOutgoingMessage(e);
    }
});

// Tự động thay đổi chiều cao ô input
messageInput.addEventListener("input", () => {
    messageInput.style.height = `${initialInputHeight}px`;
    messageInput.style.height = `${messageInput.scrollHeight}px`;
});

// Xử lý chọn file
fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        fileUploadWrapper.querySelector("img").src = e.target.result;
        fileUploadWrapper.classList.add("file-uploaded");
        userData.file = {
            data: e.target.result.split(",")[1],
            mime_type: file.type
        };
    };
    reader.readAsDataURL(file);
});

// Hủy file
fileCancelButton.addEventListener("click", () => {
    userData.file = {};
    fileUploadWrapper.classList.remove("file-uploaded");
});

// Gửi tin bằng nút
sendMessageButton.addEventListener("click", handleOutgoingMessage);

// Mở/đóng chatbot
chatbotToggler.addEventListener("click", () => document.body.classList.toggle("show-chatbot"));
closeChatbot.addEventListener("click", () => document.body.classList.remove("show-chatbot"));
