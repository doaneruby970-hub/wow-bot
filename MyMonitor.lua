-- 尝试获取 RangeDisplay 的测距库
local rc
if LibStub then
    rc = LibStub("LibRangeCheck-2.0", true)
end

local PixelFrame = CreateFrame("Frame", "MyDataBridge", UIParent)
local scale = UIParent:GetEffectiveScale()
PixelFrame:SetScale(1 / scale)

-- 【尺寸设定】10个格子 x 20像素 = 200宽度
PixelFrame:SetSize(200, 20)

-- 【关键修改】Y轴改为 0 (贴顶)，X轴保持 150 (偏右，不挡中间)
PixelFrame:SetPoint("TOP", UIParent, "TOP", 150, 0)

-- 层级设为最高，防止被其他UI遮挡
PixelFrame:SetFrameStrata("FULLSCREEN_DIALOG")

local textures = {}
for i = 1, 10 do
    textures[i] = PixelFrame:CreateTexture(nil, "OVERLAY")
    textures[i]:SetSize(20, 20)
    textures[i]:SetPoint("LEFT", (i-1)*20, 0)
    textures[i]:SetColorTexture(0, 0, 0, 1)
end

local function numToRGB(num)
    if not num then num = 0 end
    local r = math.floor(num / 256)
    local g = num % 256
    return r/255, g/255
end

local function boolToNum(val) return val and 1 or 0 end

PixelFrame:SetScript("OnUpdate", function()
    -- [1] 锚点 (粉色)
    textures[1]:SetColorTexture(1, 0, 1, 1)

    -- [2-3] HP
    local hp = UnitHealth("player")
    local hp_r, hp_g = numToRGB(hp)
    textures[2]:SetColorTexture(hp_r, 0, 0, 1)
    textures[3]:SetColorTexture(hp_g, 0, 0, 1)

    -- [4-5] MP (使用 UnitPower 防止崩溃)
    local mp = UnitPower("player")
    local mp_r, mp_g = numToRGB(mp)
    textures[4]:SetColorTexture(mp_r, 0, 0, 1)
    textures[5]:SetColorTexture(mp_g, 0, 0, 1)

    -- [6] 目标 HP%
    local t_pct = 0
    if UnitExists("target") then
        local thp = UnitHealth("target")
        local tmax = UnitHealthMax("target")
        if tmax > 0 then t_pct = math.floor((thp/tmax)*100) end
    end
    textures[6]:SetColorTexture(t_pct/255, 0, 0, 1)

    -- [7] 目标等级
    local t_lvl = UnitLevel("target")
    if t_lvl == -1 then t_lvl = 255 end
    textures[7]:SetColorTexture(t_lvl/255, 0, 0, 1)

    -- [8] 状态
    local in_combat = UnitAffectingCombat("player")
    local is_enemy = UnitCanAttack("player", "target")
    local t_dead = UnitIsDead("target")
    textures[8]:SetColorTexture(boolToNum(in_combat)/255, boolToNum(is_enemy)/255, boolToNum(t_dead)/255, 1)

    -- [9-10] 距离
    local range = 0
    if rc and UnitExists("target") then
        local minR, maxR = rc:GetRange("target")
        if minR then range = maxR or minR end
    end

    local range_int = math.floor(range * 100)
    local r_high, r_low = numToRGB(range_int)
    textures[9]:SetColorTexture(r_high, 0, 0, 1)
    textures[10]:SetColorTexture(r_low, 0, 0, 1)
end)