/* BEGIN EXTERNAL SOURCE */

/* END EXTERNAL SOURCE */
/* BEGIN EXTERNAL SOURCE */

/* END EXTERNAL SOURCE */
/* BEGIN EXTERNAL SOURCE */

    document.addEventListener("DOMContentLoaded", function () {
        var socket = io.connect('http://' + document.domain + ':' + location.port);

        function scrollToBottom() {
            var messageContainer = document.getElementById("messageContainer");
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }
        scrollToBottom();

        var currentUserName = "{{ current_user.name }}";

        window.addNewMessage = function (senderName, content) {
            var messageContainer = document.getElementById("messageContainer");
            var newMessage = document.createElement("div");
            newMessage.className = "message";
            newMessage.innerHTML = '<strong class="chat-size">' + senderName + '</strong>: ' + content;
            messageContainer.appendChild(newMessage);

            scrollToBottom();
        };

        function handleUserSelection(userId) {
            window.location.href = '/chat/' + userId;
        }

        $('.select-user .user').click(function () {
            var selectedUserId = $(this).data('user-id');
            handleUserSelection(selectedUserId);
        });

        // Handle click event for last-message-box
        $('.last-message-box').click(function () {
            var selectedUserId = $(this).data('user-id');
            handleUserSelection(selectedUserId);
        });

        $('#messageForm').submit(function (e) {
            e.preventDefault();
            var content = $('.message-input').val();

            if (content.trim() !== '') {
                $.ajax({
                    type: 'POST',
                    url: window.location.href,
                    data: { content: content },
                    success: function () {
                        $('.message-input').val('');
                    }
                });
            }
        });

        $('.message-input').keydown(function (e) {
            if (e.which === 13) {
                e.preventDefault();
                $('#messageForm').submit();
            }
        });

        socket.on('message', function (data) {
            addNewMessage(data.sender_name, data.content);
        });
    });

/* END EXTERNAL SOURCE */
