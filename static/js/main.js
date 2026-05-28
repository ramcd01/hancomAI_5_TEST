$(document).ready(function() {
    // [READ] 페이지가 로드되면 즉시 서버에서 목록을 조회하여 화면에 출력
    getTodos();

    // 💡 [추가] 필터 버튼 클릭 시 조건별 조회 이벤트
    $(document).on('click', '.btn-filter', function() {
        // 활성화 버튼 스타일 전환
        $('.btn-filter').removeClass('active');
        $(this).addClass('active');

        const filterType = $(this).data('filter');
        
        if (filterType === 'all') {
            $('.todo-item').show();
        } else if (filterType === 'active') {
            $('.todo-item').not('.completed').show(); // 완료되지 않은 항목만 조회
            $('.todo-item.completed').hide();
        } else if (filterType === 'completed') {
            $('.todo-item.completed').show();         // 완료된 항목만 조회
            $('.todo-item').not('.completed').hide();
        }
    });
    
    // [CREATE] 할 일 추가
    $('#todoForm').on('submit', function(e) {
        e.preventDefault();
        const titleText = $('#todoInput').val().trim();
        if(!titleText) return;

        $.ajax({
            url: '/todos',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ title: titleText }),
            success: function() {
                $('#todoInput').val('');
                getTodos(); // 등록 성공 시 전체 목록 최신화(조회)
            },
            error: function() {
                alert("할 일 추가에 실패했습니다.");
            }
        });
    });

    // [UPDATE] 완료 버튼 클릭 시 상태 토글 (이벤트 위임)
    $(document).on('click', '.btn-complete', function() {
        const $li = $(this).closest('.todo-item');
        const id = $li.attr('id').split('-')[1];
        
        // 현재 completed 클래스가 있으면 완료된 상태 -> 미완료(false)로 변경 예정
        // 없으면 미완료 상태 -> 완료(true)로 변경 예정
        const currentStatus = $li.hasClass('completed'); 
        const nextStatus = !currentStatus;

        $.ajax({
            url: `/todos/${id}`,
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({ completed: nextStatus }),
            success: function(response) {
                // 성공 시 화면 동적 업데이트 (조회를 다시 호출하지 않고 DOM을 직접 조작해 속도 향상)
                if (response.completed) {
                    $li.addClass('completed');
                    $li.find('.btn-complete').text('취소').addClass('status-completed');
                } else {
                    $li.removeClass('completed');
                    $li.find('.btn-complete').text('완료').removeClass('status-completed');
                }
            },
            error: function() {
                alert("완료 처리 중 오류가 발생했습니다.");
            }
        });
    });

    // [UPDATE] 수정 모드 활성화
    $(document).on('click', '.btn-edit', function() {
        $(this).closest('.todo-item').addClass('editing');
    });

    // [UPDATE] 수정 취소
    $(document).on('click', '.btn-cancel', function() {
        const $li = $(this).closest('.todo-item');
        $li.removeClass('editing');
        const originalText = $li.find('.todo-text').text();
        $li.find('.edit-input').val(originalText);
    });

    // [UPDATE] 수정 내용 저장
    $(document).on('click', '.btn-save', function() {
        const $li = $(this).closest('.todo-item');
        const id = $li.attr('id').split('-')[1];
        const updatedTitle = $li.find('.edit-input').val().trim();

        if(!updatedTitle) {
            alert("내용을 입력해주세요.");
            return;
        }

        $.ajax({
            url: `/todos/${id}`,
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({ title: updatedTitle }),
            success: function(response) {
                $li.find('.todo-text').text(response.title);
                $li.removeClass('editing');
            },
            error: function() {
                alert("내용 수정에 실패했습니다.");
            }
        });
    });

    // [DELETE] 할 일 삭제
    $(document).on('click', '.btn-delete', function() {
        if(!confirm("정말로 삭제하시겠습니까?")) return;

        const $li = $(this).closest('.todo-item');
        const id = $li.attr('id').split('-')[1];

        $.ajax({
            url: `/todos/${id}`,
            type: 'DELETE',
            success: function() {
                $li.fadeOut(300, function() {
                    $(this).remove();
                    if ($('#todoList').children().length === 0) {
                        getTodos(); // 전량 삭제 시 안내 문구 표출을 위한 재조회
                    }
                });
            },
            error: function() {
                alert("삭제 처리에 실패했습니다.");
            }
        });
    });
});

// [READ] 백엔드 DB 서버로부터 데이터를 실시간 조회하여 리스트 생성
function getTodos() {
    $.ajax({
        url: '/todos',
        type: 'GET',
        dataType: 'json',
        success: function(todos) {
            const $todoList = $('#todoList');
            $todoList.empty();

            if(todos.length === 0) {
                $todoList.append(`
                    <li class="no-item" id="noItemMessage">
                        등록된 할 일이 없습니다. 오늘 할 일을 추가해 보세요!
                    </li>
                `);
                return;
            }

            todos.forEach(function(todo) {
                // DB 데이터 기반 분기 처리
                const completedClass = todo.completed ? 'completed' : '';
                const buttonText = todo.completed ? '취소' : '완료';
                const buttonClass = todo.completed ? 'status-completed' : '';

                const itemHtml = `
                    <li class="todo-item ${completedClass}" id="todo-${todo.id}">
                        <div class="todo-left">
                            <span class="todo-text">${todo.title}</span>
                            <input type="text" class="edit-input" value="${todo.title}">
                        </div>
                        <div class="todo-buttons">
                            <button class="btn-complete ${buttonClass}">${buttonText}</button>
                            <button class="btn-edit">수정</button>
                            <button class="btn-delete">삭제</button>
                            
                            <button class="btn-save">저장</button>
                            <button class="btn-cancel">취소</button>
                        </div>
                    </li>
                `;
                $todoList.append(itemHtml);
            });
        },
        error: function() {
            $('#todoList').html('<li class="no-item" style="color: red;">데이터를 불러오는 데 실패했습니다.</li>');
        }
    });
}