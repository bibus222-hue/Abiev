// В методе инициализации мира или загрузки уровня
private void initializeBlockedCells() {
    // Добавляем новую заблокированную клетку
    GridPos newBlockedCell = new GridPos(-2, 0);
    blockedCells.add(newBlockedCell);
    
    // Добавляем её же в wallCells в world-сцене
    worldScene.addWallCell(newBlockedCell);
}

// В классе PlayerController или GameScreen
public class PlayerController {
    private static final int DASH_DISTANCE = 2;
    
    public boolean dashForward(Player player, List<GridPos> blockedCells, 
List<GridPos> wallCells, GameMap gameMap) {
        GridPos currentPos = player.getGridPosition();
        GridPos targetPos = calculateDashPosition(currentPos, DASH_DISTANCE);
        
        // Проверяем путь на препятствия
        if (isPathClear(currentPos, targetPos, blockedCells, wallCells, gameMap)) {
            // Выполняем рывок
            player.setGridPosition(targetPos);
            player.addToHistory("dash_" + System.currentTimeMillis());
            return true;
        } else {
            System.out.println("Dash blocked! Path is not clear.");
            return false;
        }
    }
    
    private GridPos calculateDashPosition(GridPos current, int distance) {
        // Предполагаем, что направление вперёд - это ось Y
        return new GridPos(current.x, current.y + distance);
    }
    
    private boolean isPathClear(GridPos from, GridPos to, 
                                List<GridPos> blockedCells,
                                List<GridPos> wallCells, 
                                GameMap gameMap) {
        int stepX = Integer.compare(to.x, from.x);
        int stepY = Integer.compare(to.y, from.y);
        
        GridPos checkPos = new GridPos(from.x, from.y);
        
        // Проверяем каждую клетку на пути (включая целевую)
        while (!checkPos.equals(to)) {
            checkPos = new GridPos(checkPos.x + stepX, checkPos.y + stepY);
            
            // Проверка на блокировку
            if (blockedCells.contains(checkPos) || 
                wallCells.contains(checkPos) ||
                gameMap.isOutOfBounds(checkPos)) {
                return false;
            }
            
            // Проверка на других игроков (если есть)
            if (isOtherPlayerAtPosition(checkPos)) {
                return false;
            }
        }
        
        return true;
    }
    
    private boolean isOtherPlayerAtPosition(GridPos pos) {
        // Логика проверки других игроков
        return false;
    }
}

// Добавляем кнопку в UI
private void addDashButton() {
    TextButton dashButton = new TextButton("Dash Forward", skin);
    dashButton.addListener(event -> {
        if (event instanceof ClickEvent) {
            boolean success = playerController.dashForward(
                player, blockedCells, wallCells, gameMap
            );
            if (!success) {
                showMessage("Cannot dash! Path is blocked!");
            }
        }
        return false;
    });
    uiTable.add(dashButton).pad(5);
}

// В классе PlayerState
public class PlayerState {
    private Map<String, Integer> collectedHerbFromSource = new HashMap<>();
    
    public boolean canCollectHerb(String sourceId) {
        int collectedCount = collectedHerbFromSource.getOrDefault(sourceId, 0);
        return collectedCount < 3;
    }
    
    public void collectHerb(String sourceId) {
        int currentCount = collectedHerbFromSource.getOrDefault(sourceId, 0);
        if (currentCount < 3) {
            collectedHerbFromSource.put(sourceId, currentCount + 1);
        }
    }
    
    public int getHerbCollectedCount(String sourceId) {
        return collectedHerbFromSource.getOrDefault(sourceId, 0);
    }
}

// В серверной логике или классе взаимодействия
public class HerbInteraction {
    private PlayerState playerState;
    private Map<String, Integer> herbSources = new HashMap<>();
    
    public boolean collectHerb(Player player, String sourceId) {
        // Проверяем, не иссяк ли источник
        if (!herbSources.containsKey(sourceId)) {
            // Инициализируем источник (макс 3 сбора)
            herbSources.put(sourceId, 3);
        }
        
        int remainingUses = herbSources.get(sourceId);
        
        if (remainingUses <= 0) {
            sendServerMessage("Источник Herb уже пуст");
            return false;
        }
        
        // Проверяем, сколько раз игрок уже собрал с этого источника
        if (!playerState.canCollectHerb(sourceId)) {
            sendServerMessage("Вы уже собрали весь herb с этого источника!");
            return false;
        }
        
        // Собираем herb
        playerState.collectHerb(sourceId);
        herbSources.put(sourceId, remainingUses - 1);
        
        // Добавляем herb в инвентарь игрока
        player.addItem("herb", 1);
        
        sendServerMessage("Вы собрали herb! Осталось сборов: " + (remainingUses - 1));
        
        // Если источник иссяк, удаляем его или меняем визуал
        if (remainingUses - 1 <= 0) {
            deactivateHerbSource(sourceId);
            sendServerMessage("Источник herb иссяк!");
        }
        
        return true;
    }
    
    private void sendServerMessage(String message) {
        System.out.println("[SERVER]: " + message);
        // Здесь отправка сообщения клиенту
    }
    
    private void deactivateHerbSource(String sourceId) {
        // Меняем визуал источника или удаляем его с карты
        // Например: замена текстуры или удаление объекта
    }
}

// Пример использования в игре
public class GameInteraction {
    public void onHerbCollect(Player player, HerbSource source) {
        String sourceId = source.getId();
        
        if (herbInteraction.collectHerb(player, sourceId)) {
            // Обновляем визуал источника
            source.updateVisual(getRemainingUses(sourceId));
            
            // Обновляем UI игрока
            updateInventoryDisplay();
        }
    }
}

// Добавляем задержку между рывками
public class DashController {
    private long lastDashTime = 0;
    private static final long DASH_COOLDOWN_MS = 3000;
    
    public boolean tryDash(Player player) {
        long currentTime = System.currentTimeMillis();
        
        if (currentTime - lastDashTime < DASH_COOLDOWN_MS) {
            long remainingCooldown = DASH_COOLDOWN_MS - (currentTime - lastDashTime);
            System.out.println("Dash on cooldown! " + remainingCooldown/1000 + "s remaining");
            return false;
        }
        
        boolean success = player.dashForward();
        if (success) {
            lastDashTime = currentTime;
        }
        return success;
    }
}

@Test
public void testHerbCollectionLimit() {
    PlayerState state = new PlayerState();
    String sourceId = "test_source";
    
    // Первые 3 сбора должны быть успешны
    for (int i = 0; i < 3; i++) {
        assertTrue(state.canCollectHerb(sourceId));
        state.collectHerb(sourceId);
    }
    
    // 4-й сбор должен быть невозможен
    assertFalse(state.canCollectHerb(sourceId));
}

@Test
public void testDashThroughWalls() {
    // Создаём стену на пути даша
    GridPos wallPos = new GridPos(0, 1);
    wallCells.add(wallPos);
    
    Player player = new Player(new GridPos(0, 0));
    boolean dashSuccess = playerController.dashForward(player, blockedCells, wallCells, gameMap);
    
    assertFalse(dashSuccess); // Даш должен провалиться
    assertEquals(new GridPos(0, 0), player.getGridPosition()); // Позиция не изменилась
}