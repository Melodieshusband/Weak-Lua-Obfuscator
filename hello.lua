local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local LocalPlayer = Players.LocalPlayer

local Hub = loadstring(game:HttpGet("https://raw.githubusercontent.com/Okaygotenitsme/MelotenHub/main/Meloten_Template.lua"))()

local Window = Hub:CreateWindow({
	Title = "The Strongest Battlegrounds | Meloten Hub",
	Icon = "https://raw.githubusercontent.com/Okaygotenitsme/MelotenHub/main/Meloten_logo.png",
	Size = {X = 480, Y = 340}
})

local MainTab = Window:AddTab("Main")
local TeleportTab = Window:AddTab("Teleport")
local SillyTab = Window:AddTab("Silly")
local AntiSkillsTab = Window:AddTab("Anti Skills")

local TeleportAreas = {
	["Death Counter"] = CFrame.new(-66, 29, 20383) * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0),
	["Middle"] = CFrame.new(155, 441, 45) * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0),
	["Mountain"] = CFrame.new(306, 671, 411) * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0),
	["Arena"] = CFrame.new(-130, 440, -373) * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0),
	["Jail"] = CFrame.new(440, 440, -395) * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0),
	["Bigger Jail"] = CFrame.new(290, 440, 465) * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0),
	["Dark Domain"] = CFrame.new(-80, 84, 20395) * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0),
	["Void"] = CFrame.new(169, 218, 102) * CFrame.new(0, 1.5, 0) * CFrame.Angles(math.rad(90), 0, 0),
}

local Configuration = {
	WallComboAnywhere = false,
	AutoWallComboMode = "Auto Wall Combo + Bring",
	AutoWallComboTPBack = false,
	AutoWallComboArea = "Death Counter"
}

local DesyncState = {
	IsActive = false,
	TargetCFrame = nil
}

local FlyState = {
	Enabled = false,
	Active = false,
	Speed = 150,
	SavedCFrame = nil
}

local SpeedState = {
	Enabled = false,
	Speed = 100
}

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Features = {
	Anti_AntiCheat = false,
	Staff_Detector = false,
}

local StaffIds = {
	422755031, 198131804, 681405668, 3414432341, 339633571,
	430966809, 2039323684, 117723419, 1015595932, 263944298,
	112905203, 2284964418, 1266437961, 3120648134, 1148139861,
	1633233654, 3350014406, 971193650, 661273560, 66105529,
	77342385, 167343092, 2055306963, 141984224, 438917845,
	1391134999, 1796550069, 255671730, 3162123826, 1059541187,
	1259898795, 31070091, 1041867508, 994994173, 1446694201,
	77525605, 1001242712, 2533866869, 4983064295,
}

local function notifyStaff(player)
	if player == LocalPlayer then return end
	local displayName = player.DisplayName
	if player:IsInGroup(12013007) then
		local role = player:GetRoleInGroup(12013007)
		if role then
			game:GetService("StarterGui"):SetCore("SendNotification", {
				Title = "Staff Detector",
				Text = displayName .. " is in your game! (" .. role .. ")",
				Duration = 10,
			})
		end
	end
	for _, id in ipairs(StaffIds) do
		if player.UserId == id then
			game:GetService("StarterGui"):SetCore("SendNotification", {
				Title = "Staff Detector",
				Text = "A special person joined: " .. displayName,
				Duration = 10,
			})
			return
		end
	end
end

if Features.Staff_Detector then
	for _, player in ipairs(Players:GetPlayers()) do
		task.spawn(pcall, notifyStaff, player)
	end

	Players.PlayerAdded:Connect(function(player)
		task.spawn(pcall, notifyStaff, player)
	end)
end

if Features.Anti_AntiCheat then
	task.spawn(function()
		local ok, replication = pcall(function()
			return ReplicatedStorage:WaitForChild("Replication", 10)
		end)
		if not ok or not replication then return end
		replication.OnClientEvent:Connect(function(...)
			local data = select(1, ...)
			if data then
				local effect = rawget(data, "Effect") or "Unknown"
				if effect:lower() == "hicheck" then
					game:GetService("StarterGui"):SetCore("SendNotification", {
						Title = "Anticheat Flagged",
						Text = "A1 (Report) - server detected you",
						Duration = 10,
					})
				end
			end
		end)
	end)

	local function connectAnimationAC(character)
		local humanoid = character:WaitForChild("Humanoid")
		local animator = humanoid:WaitForChild("Animator")
		animator.AnimationPlayed:Connect(function(track)
			local anim = track.Animation
			if anim and anim.AnimationId:match("18748398210") then
				game:GetService("StarterGui"):SetCore("SendNotification", {
					Title = "Anticheat Flagged",
					Text = "A2 (Animation) - AC animation played",
					Duration = 10,
				})
			end
		end)
	end

	if LocalPlayer.Character then
		task.spawn(connectAnimationAC, LocalPlayer.Character)
	end

	LocalPlayer.CharacterAdded:Connect(function(character)
		task.spawn(connectAnimationAC, character)
	end)
end

local function communicate(actionData)
	local character = LocalPlayer.Character
	if character then
		local communicator = character:FindFirstChild("Communicate")
		if communicator then
			communicator:FireServer(actionData)
		end
	end
end

local function stopAllAnimations(humanoid)
	if humanoid then
		for _, track in ipairs(humanoid:GetPlayingAnimationTracks()) do
			track:Stop()
		end
	end
end

RunService.Heartbeat:Connect(function()
	if DesyncState.IsActive and DesyncState.TargetCFrame then
		local character = LocalPlayer.Character
		if character then
			local rootPart = character:FindFirstChild("HumanoidRootPart")
			if rootPart then
				rootPart.Velocity = Vector3.new(0, 0, 0)
				rootPart.RotVelocity = Vector3.new(0, 0, 0)
				rootPart.CFrame = DesyncState.TargetCFrame
			end
		end
	end
end)

local flyConnection = nil

local function startFly()
	if flyConnection then flyConnection:Disconnect() end
	local character = LocalPlayer.Character
	if not character then return end
	local rootPart = character:FindFirstChild("HumanoidRootPart")
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if not rootPart or not humanoid then return end

	FlyState.SavedCFrame = rootPart.CFrame
	FlyState.Active = true

	flyConnection = RunService.Heartbeat:Connect(function()
		if not FlyState.Active or not FlyState.Enabled then
			FlyState.Active = false
			if flyConnection then flyConnection:Disconnect() flyConnection = nil end
			return
		end
		local char = LocalPlayer.Character
		if not char then return end
		local root = char:FindFirstChild("HumanoidRootPart")
		local hum = char:FindFirstChildOfClass("Humanoid")
		local cam = workspace.CurrentCamera
		if not root or not hum or not cam then return end

		local speed = FlyState.Speed / 100
		local vel = Vector3.new(0, 0, 0)
		local camCF = cam.CFrame
		local look = camCF.LookVector
		local right = camCF.RightVector
		local flatLook = CFrame.new(root.Position, root.Position + Vector3.new(look.X, 0, look.Z))
		local fwd = math.round(hum.MoveDirection:Dot(flatLook.LookVector))
		local side = math.round(hum.MoveDirection:Dot(flatLook.RightVector))

		if fwd == 1 then vel = vel + look * speed end
		if fwd == -1 then vel = vel + -look * speed end
		if side == 1 then vel = vel + right * speed end
		if side == -1 then vel = vel + -right * speed end

		if fwd == 0 and side == 0 then
			root.Velocity = Vector3.new()
			root.CFrame = FlyState.SavedCFrame or root.CFrame
		else
			root.Velocity = vel
			FlyState.SavedCFrame = root.CFrame
		end
		root.RotVelocity = Vector3.new()
		root.CFrame = CFrame.new(root.Position, root.Position + Vector3.new(look.X, 0, look.Z))
	end)
end

local function stopFly()
	FlyState.Active = false
	if flyConnection then
		flyConnection:Disconnect()
		flyConnection = nil
	end
end

local speedConnection = nil

local function startSpeedHack()
	if speedConnection then speedConnection:Disconnect() end
	speedConnection = RunService.Heartbeat:Connect(function()
		if not SpeedState.Enabled then
			speedConnection:Disconnect()
			speedConnection = nil
			return
		end
		local char = LocalPlayer.Character
		if not char then return end
		local root = char:FindFirstChild("HumanoidRootPart")
		local hum = char:FindFirstChildOfClass("Humanoid")
		if not root or not hum then return end
		if hum.MoveDirection.Magnitude > 0 then
			root.Velocity = hum.MoveDirection * SpeedState.Speed
		end
	end)
end

local invisConnection = nil

local noStunConnection = nil

local function onCharacterAdded(character)
	local rootPart = character:WaitForChild("HumanoidRootPart")
	local humanoid = character:WaitForChild("Humanoid")

	character.AttributeChanged:Connect(function(attributeName)
		if attributeName == "Combo" and character:GetAttribute("Combo") == 5 and rootPart then
			if Configuration.WallComboAnywhere then
				if Configuration.AutoWallComboMode == "Auto Wall Combo + Bring" then
					local startTime = tick()

					DesyncState.TargetCFrame = rootPart.CFrame * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0)
					DesyncState.IsActive = true

					repeat
						task.wait()
					until tick() >= startTime + 0.225

					local originalCFrame = rootPart.CFrame
					local targetArea = TeleportAreas[Configuration.AutoWallComboArea] or originalCFrame

					DesyncState.TargetCFrame = targetArea
					task.wait(0.2)

					communicate({Goal = "Wall Combo"})

					DesyncState.IsActive = false
					DesyncState.TargetCFrame = nil
					task.wait(0.5)

					if Configuration.AutoWallComboTPBack then
						stopAllAnimations(humanoid)
						rootPart.CFrame = originalCFrame
					end
				else
					local startTime = tick()

					DesyncState.TargetCFrame = rootPart.CFrame * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0)
					DesyncState.IsActive = true

					repeat
						task.wait()
					until tick() >= startTime + 0.6

					DesyncState.IsActive = false
					DesyncState.TargetCFrame = nil
				end
			end
		end
	end)

	character.DescendantAdded:Connect(function(descendant)
		if descendant:IsA("ObjectValue") and descendant.Name:lower() == "wallcombo" then
			local startTime = tick()

			while true do
				if Configuration.AutoWallComboMode == "Auto Wall Combo" then
					communicate({Goal = "Wall Combo"})
				end

				task.wait()

				if descendant.Parent ~= character or tick() >= startTime + (descendant:GetAttribute("DeleteMe") or 0.6) then
					break
				end
			end
		end
	end)
end

if LocalPlayer.Character then
	task.spawn(onCharacterAdded, LocalPlayer.Character)
end

LocalPlayer.CharacterAdded:Connect(onCharacterAdded)

local FLIP_TARGET_IDS = {
	["12273188754"] = true,
	["14374357351"] = true
}
local EARLY_END_ANIM_ID = "12273188754"
local EARLY_END_SECONDS = 0.5
local FLIP_HEIGHT_OFFSET = 3

local flipEnabled = false
local flipLockedY = nil

local function getFlipAnimator()
	local character = LocalPlayer.Character
	if not character then return nil end
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if not humanoid then return nil end
	return humanoid:FindFirstChildOfClass("Animator")
end

local function shouldFlipNow()
	local animator = getFlipAnimator()
	if not animator then return false end
	for _, track in ipairs(animator:GetPlayingAnimationTracks()) do
		local anim = track.Animation
		if anim then
			local id = anim.AnimationId:match("(%d+)")
			if id and FLIP_TARGET_IDS[id] then
				if id == EARLY_END_ANIM_ID then
					local length = track.Length
					local timePos = track.TimePosition
					if length > 0 and (length - timePos) <= EARLY_END_SECONDS then
						return false
					end
				end
				return true
			end
		end
	end
	return false
end

RunService.RenderStepped:Connect(function()
	if not flipEnabled then
		flipLockedY = nil
		return
	end
	local character = LocalPlayer.Character
	if not character then return end
	local rootPart = character:FindFirstChild("HumanoidRootPart")
	if not rootPart then return end

	if shouldFlipNow() then
		if not flipLockedY then
			flipLockedY = rootPart.Position.Y + FLIP_HEIGHT_OFFSET
		end
		local cf = rootPart.CFrame
		local pos = Vector3.new(cf.Position.X, flipLockedY, cf.Position.Z)
		rootPart.CFrame = CFrame.new(pos) * CFrame.Angles(math.rad(180), 0, 0)
	else
		flipLockedY = nil
	end
end)

local function enableNoStun()
	local character = LocalPlayer.Character
	if not character then return end
	if noStunConnection then noStunConnection:Disconnect() end
	noStunConnection = character.ChildAdded:Connect(function(c)
		if c.Name == "Freeze" or c.Name == "ComboStun" then
			task.wait()
			c:Destroy()
		end
	end)
end

local function disableNoStun()
	if noStunConnection then
		noStunConnection:Disconnect()
		noStunConnection = nil
	end
end

MainTab:AddButton("Teleport to Middle", "Teleport", function()
	local character = LocalPlayer.Character
	if character then
		local rootPart = character:FindFirstChild("HumanoidRootPart")
		if rootPart then
			rootPart.CFrame = TeleportAreas["Middle"]
		end
	end
end)

MainTab:AddSection("Wall Combo")

MainTab:AddToggle("Wall Combo Anywhere", function(state)
	Configuration.WallComboAnywhere = state
end)

MainTab:AddToggle("TP Back After Combo", function(state)
	Configuration.AutoWallComboTPBack = state
end)

MainTab:AddDropdown("Mode", {
	"Auto Wall Combo + Bring",
	"Auto Wall Combo"
}, function(selected)
	Configuration.AutoWallComboMode = selected
end)

MainTab:AddDropdown("Teleport Area", {
	"Death Counter",
	"Middle"
}, function(selected)
	Configuration.AutoWallComboArea = selected
end)

MainTab:AddSection("Combat")

MainTab:AddToggle("No Stun", function(state)
	if state then
		enableNoStun()
		LocalPlayer.CharacterAdded:Connect(function()
			task.wait(0.5)
			enableNoStun()
		end)
	else
		disableNoStun()
	end
end)

MainTab:AddToggle("Inf Dash", function(state)
	if state then
		workspace:SetAttribute("VIPServerOwner", LocalPlayer.Name)
		workspace:SetAttribute("VIPServer", LocalPlayer.UserId)
		workspace:SetAttribute("CommandTarget", 1)
		workspace:SetAttribute("EffectAffects", true)
		workspace:SetAttribute("NoDashCooldown", true)
	else
		workspace:SetAttribute("NoDashCooldown", false)
	end
end)

MainTab:AddSection("Auto Farm")

local autoFarmEnabled = false
local autoFarmStickOffset = Vector3.new(0, -5, 0)
local autoFarmTarget = nil
local autoFarmTargetConn = nil
local farmByLowestHp = false
local autoFarmPinnedName = nil

local function isTargetValid(p)
	if not p or not p.Parent then return false end
	if not p.Character then return false end
	local hum = p.Character:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 then return false end
	if not p.Character:FindFirstChild("HumanoidRootPart") then return false end
	return true
end

local function clearAutoFarmTarget()
	autoFarmTarget = nil
	if autoFarmTargetConn then
		autoFarmTargetConn:Disconnect()
		autoFarmTargetConn = nil
	end
end

local function findClosestPlayer()
	local character = LocalPlayer.Character
	if not character or not character:FindFirstChild("HumanoidRootPart") then return nil end
	local myPos = character.HumanoidRootPart.Position
	local closest, shortest = nil, math.huge
	for _, p in ipairs(Players:GetPlayers()) do
		if isTargetValid(p) and p ~= LocalPlayer then
			local dist = (p.Character.HumanoidRootPart.Position - myPos).Magnitude
			if dist < shortest then
				shortest = dist
				closest = p
			end
		end
	end
	return closest
end

local function lockOnTarget(p)
	clearAutoFarmTarget()
	autoFarmTarget = p

	local hum = p.Character:FindFirstChildOfClass("Humanoid")
	autoFarmTargetConn = hum.Died:Connect(function()
		clearAutoFarmTarget()
	end)

	p.CharacterRemoving:Connect(function()
		if autoFarmTarget == p then
			clearAutoFarmTarget()
		end
	end)

	Players.PlayerRemoving:Connect(function(leaving)
		if leaving == p then
			clearAutoFarmTarget()
		end
	end)
end

local function findLowestHpPlayer()
	local picked, lowestHp = nil, math.huge
	for _, p in ipairs(Players:GetPlayers()) do
		if isTargetValid(p) and p ~= LocalPlayer then
			local hum = p.Character:FindFirstChildOfClass("Humanoid")
			if hum and hum.Health < lowestHp then
				lowestHp = hum.Health
				picked = p
			end
		end
	end
	return picked
end

local function findPlayerByName(name)
	local lname = name:lower()
	for _, p in ipairs(Players:GetPlayers()) do
		if p ~= LocalPlayer and p.Name:lower() == lname or p.DisplayName:lower() == lname then
			if isTargetValid(p) then return p end
		end
	end
	return nil
end

RunService.Heartbeat:Connect(function()
	if not autoFarmEnabled then return end
	local character = LocalPlayer.Character
	if not character then return end
	local rootPart = character:FindFirstChild("HumanoidRootPart")
	if not rootPart then return end

	if not isTargetValid(autoFarmTarget) then
		local found
		if autoFarmPinnedName and autoFarmPinnedName ~= "" then
			found = findPlayerByName(autoFarmPinnedName)
		elseif farmByLowestHp then
			found = findLowestHpPlayer()
		else
			found = findClosestPlayer()
		end
		if found then
			lockOnTarget(found)
		else
			return
		end
	end

	local targetRoot = autoFarmTarget.Character:FindFirstChild("HumanoidRootPart")
	if not targetRoot then return end
	local newPos = targetRoot.Position + autoFarmStickOffset
	rootPart.CFrame = CFrame.new(newPos, newPos + Vector3.new(0, 1, 0))
end)

MainTab:AddToggle("Auto Farm", function(state)
	autoFarmEnabled = state
	if not state then
		clearAutoFarmTarget()
	end
end)

MainTab:AddToggle("Target Lowest HP", function(state)
	farmByLowestHp = state
	clearAutoFarmTarget()
end)

MainTab:AddInput("Pin Target", "Player name...", function(text)
	autoFarmPinnedName = text ~= "" and text or nil
	clearAutoFarmTarget()
end)

MainTab:AddSection("Collect All")

local TweenService = game:GetService("TweenService")

local CollectAllConfig = {
	AttackAll = false,
	AttackAllMoves = {
		["Twin Fangs"] = false,
		["Savage Tornado"] = false,
		["Brutal Beatdown"] = false,
		["Crushed Rock Variant"] = false,
	}
}

local COLLECT_ALL_ANIM_IDS = {
	["Twin Fangs"]        = "18896229321",
	["Savage Tornado"]     = "14719290328",
	["Brutal Beatdown"]    = "14701242661",
	["Crushed Rock Variant"] = "135104210400610",
}

local SAFE_PLATFORM_POS = Vector3.new(0, 10000, 0)
local CollectAllJailCFrame = CFrame.new(378, 439, 457) * CFrame.new(0, -0.5, 0) * CFrame.Angles(math.rad(-90), 0, 0)

local safePlatform = Instance.new("Part")
safePlatform.Size = Vector3.new(200, 5, 200)
safePlatform.CFrame = CFrame.new(SAFE_PLATFORM_POS)
safePlatform.Anchored = true
safePlatform.CanCollide = true
safePlatform.Material = Enum.Material.SmoothPlastic
safePlatform.BrickColor = BrickColor.new("Medium stone grey")
safePlatform.Name = "CollectAllPlatform"
safePlatform.Parent = workspace

local CollectAllVoidCFrame = CFrame.new(SAFE_PLATFORM_POS + Vector3.new(0, 5, 0))

local function collectAllGetPlayers()
	local list = Players:GetPlayers()
	table.remove(list, table.find(list, LocalPlayer))
	return list
end

local function collectAllTp(targetCFrame)
	local character = LocalPlayer.Character
	if not character then return end
	local rootPart = character:FindFirstChild("HumanoidRootPart")
	if rootPart then
		rootPart.CFrame = targetCFrame
	end
end

local function isDeathBlowPresent(character, humanoid)
	for _, tool in ipairs(character:GetChildren()) do
		if tool:IsA("Tool") and tool.Name == "Death Blow" then return true end
	end
	for _, track in ipairs(humanoid:GetPlayingAnimationTracks()) do
		if track.Animation.AnimationId == "rbxassetid://15128849047" then return true end
	end
	return false
end

local function grabRandomPlayer(checkDeathBlow)
	local allPlayers = collectAllGetPlayers()
	if #allPlayers == 0 then return end
	local randomPlayer = allPlayers[math.random(1, #allPlayers)]

	local myCharacter = LocalPlayer.Character
	local myRoot = myCharacter and myCharacter:FindFirstChild("HumanoidRootPart")
	local targetCharacter = randomPlayer.Character
	local targetRoot = targetCharacter and targetCharacter:FindFirstChild("HumanoidRootPart")
	local targetHumanoid = targetCharacter and targetCharacter:FindFirstChild("Humanoid")

	if not (myRoot and targetRoot and targetHumanoid) then return end

	if checkDeathBlow then
		if isDeathBlowPresent(targetCharacter, targetHumanoid) then return end
		for _, otherPlayer in ipairs(Players:GetPlayers()) do
			if otherPlayer == LocalPlayer or otherPlayer == randomPlayer then continue end
			local otherChar = otherPlayer.Character
			local otherRoot = otherChar and otherChar:FindFirstChild("HumanoidRootPart")
			local otherHum = otherChar and otherChar:FindFirstChild("Humanoid")
			if otherRoot and otherHum and (otherRoot.Position - targetRoot.Position).Magnitude <= 100 then
				if isDeathBlowPresent(otherChar, otherHum) then return end
			end
		end
	end

	collectAllTp(targetRoot.CFrame)
	task.wait()
	collectAllTp(CFrame.lookAt(myRoot.Position, targetRoot.Position))
end

local function getPlayingAnimTrack(animId)
	local character = LocalPlayer.Character
	if not character then return nil end
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if not humanoid then return nil end
	local animator = humanoid:FindFirstChildOfClass("Animator")
	if not animator then return nil end
	for _, track in ipairs(animator:GetPlayingAnimationTracks()) do
		local anim = track.Animation
		if anim and anim.AnimationId:match(animId) then
			return track
		end
	end
	return nil
end

local twinFangsRunning = false

local function runTwinFangs(animTrack)
	if twinFangsRunning then return end
	twinFangsRunning = true

	local character = LocalPlayer.Character
	local myRoot = character and character:FindFirstChild("HumanoidRootPart")
	if not myRoot then twinFangsRunning = false return end

	local originalCFrame = myRoot.CFrame
	collectAllTp(CollectAllVoidCFrame)
	task.wait(0.5)

	local startTime = tick()
	repeat
		grabRandomPlayer(true)
		task.wait(0.03)
	until tick() >= startTime + 1.5 or not animTrack.IsPlaying

	collectAllTp(originalCFrame)
	twinFangsRunning = false
end

-- Savage Tornado logic
local savageRunning = false

local function runSavageTornado(animTrack)
	if savageRunning then return end
	savageRunning = true

	local character = LocalPlayer.Character
	local myRoot = character and character:FindFirstChild("HumanoidRootPart")
	if not myRoot then savageRunning = false return end

	local originalCFrame = myRoot.CFrame
	collectAllTp(CollectAllVoidCFrame)
	task.wait(0.9)

	local startTime = tick()
	repeat
		grabRandomPlayer(true)
		task.wait(0.03)
	until tick() >= startTime + 1.75

	TweenService:Create(myRoot, TweenInfo.new(0.35, Enum.EasingStyle.Linear, Enum.EasingDirection.InOut), {
		CFrame = CollectAllJailCFrame
	}):Play()
	task.wait(1.5)
	collectAllTp(originalCFrame)

	savageRunning = false
end

-- Brutal Beatdown logic
local brutalRunning = false

local function runBrutalBeatdown(animTrack)
	if brutalRunning then return end
	brutalRunning = true

	local character = LocalPlayer.Character
	local myRoot = character and character:FindFirstChild("HumanoidRootPart")
	if not myRoot then brutalRunning = false return end

	collectAllTp(CollectAllVoidCFrame)
	task.wait(2)

	local startTime = tick()
	repeat
		grabRandomPlayer(true)
		task.wait(0.05)
	until tick() >= startTime + 4.5

	grabRandomPlayer(true)
	task.wait(0.03)

	brutalRunning = false
end

-- Crushed Rock Variant logic
local crushedRunning = false

local function runCrushedRock(animTrack)
	if crushedRunning then return end
	crushedRunning = true

	local targetPlayer = nil
	for _, player in ipairs(collectAllGetPlayers()) do
		local character = player.Character
		local forceField = character and character:FindFirstChildWhichIsA("ForceField")
		if character and not (forceField or character:GetAttribute("CrushedRockVariant")) then
			targetPlayer = player
			break
		end
	end

	if targetPlayer then
		local targetChar = targetPlayer.Character
		local targetRoot = targetChar and targetChar:FindFirstChild("HumanoidRootPart")
		if targetRoot then
			repeat
				collectAllTp(targetRoot.CFrame)
				task.wait()
			until not animTrack.IsPlaying
		end
	end

	crushedRunning = false
end

-- Main watcher loop
task.spawn(function()
	while true do
		task.wait(0.05)
		if not CollectAllConfig.AttackAll then continue end

		if CollectAllConfig.AttackAllMoves["Twin Fangs"] and not twinFangsRunning then
			local track = getPlayingAnimTrack(COLLECT_ALL_ANIM_IDS["Twin Fangs"])
			if track then task.spawn(runTwinFangs, track) end
		end

		if CollectAllConfig.AttackAllMoves["Savage Tornado"] and not savageRunning then
			local track = getPlayingAnimTrack(COLLECT_ALL_ANIM_IDS["Savage Tornado"])
			if track then task.spawn(runSavageTornado, track) end
		end

		if CollectAllConfig.AttackAllMoves["Brutal Beatdown"] and not brutalRunning then
			local track = getPlayingAnimTrack(COLLECT_ALL_ANIM_IDS["Brutal Beatdown"])
			if track then task.spawn(runBrutalBeatdown, track) end
		end

		if CollectAllConfig.AttackAllMoves["Crushed Rock Variant"] and not crushedRunning then
			local track = getPlayingAnimTrack(COLLECT_ALL_ANIM_IDS["Crushed Rock Variant"])
			if track then task.spawn(runCrushedRock, track) end
		end
	end
end)

MainTab:AddToggle("Collect All", function(state)
	CollectAllConfig.AttackAll = state
end)

MainTab:AddToggle("Twin Fangs", function(state)
	CollectAllConfig.AttackAllMoves["Twin Fangs"] = state
end)

MainTab:AddToggle("Savage Tornado", function(state)
	CollectAllConfig.AttackAllMoves["Savage Tornado"] = state
end)

MainTab:AddToggle("Brutal Beatdown", function(state)
	CollectAllConfig.AttackAllMoves["Brutal Beatdown"] = state
end)

MainTab:AddToggle("Crushed Rock Variant", function(state)
	CollectAllConfig.AttackAllMoves["Crushed Rock Variant"] = state
end)

MainTab:AddSection("Movement")

MainTab:AddToggle("Fly (works poorly)", function(state)
	FlyState.Enabled = state
	if state then
		startFly()
	else
		stopFly()
	end
end)

MainTab:AddSlider("Fly Speed", 50, 5000, 150, function(value)
	FlyState.Speed = value
end)

MainTab:AddToggle("Speed Hack", function(state)
	SpeedState.Enabled = state
	if state then
		startSpeedHack()
	end
end)

MainTab:AddSlider("Speed", 16, 500, 100, function(value)
	SpeedState.Speed = value
end)



local FALL_BOOST_ANIM_ID = "12296113986"
local FALL_BOOST_DELAY = 1.3
local FALL_BOOST_HEIGHT = 200
local fallBoostEnabled = false
local fallBoostActive = false

local function getFallBoostAnimator()
	local character = LocalPlayer.Character
	if not character then return nil end
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if not humanoid then return nil end
	return humanoid:FindFirstChildOfClass("Animator")
end

local function isFallBoostAnimPlaying()
	local animator = getFallBoostAnimator()
	if not animator then return false, nil end
	for _, track in ipairs(animator:GetPlayingAnimationTracks()) do
		local anim = track.Animation
		if anim then
			local id = anim.AnimationId:match("(%d+)")
			if id == FALL_BOOST_ANIM_ID then
				return true, track
			end
		end
	end
	return false, nil
end

task.spawn(function()
	while true do
		task.wait(0.1)
		if not fallBoostEnabled or fallBoostActive then continue end

		local playing, track = isFallBoostAnimPlaying()
		if not playing then continue end

		fallBoostActive = true
		task.wait(FALL_BOOST_DELAY)

		local character = LocalPlayer.Character
		if not character then fallBoostActive = false continue end
		local rootPart = character:FindFirstChild("HumanoidRootPart")
		if not rootPart then fallBoostActive = false continue end

		local originalCFrame = rootPart.CFrame
		rootPart.CFrame = originalCFrame + Vector3.new(0, FALL_BOOST_HEIGHT, 0)

		local stillPlaying, currentTrack = isFallBoostAnimPlaying()
		while stillPlaying and currentTrack do
			task.wait(0.05)
			stillPlaying, currentTrack = isFallBoostAnimPlaying()
			if not stillPlaying or not currentTrack then break end

			local timeLeft = currentTrack.Length - currentTrack.TimePosition
			if timeLeft <= 0.25 then break end

			if rootPart and rootPart.Parent then
				rootPart.CFrame = CFrame.new(
					rootPart.Position.X,
					originalCFrame.Position.Y + FALL_BOOST_HEIGHT,
					rootPart.Position.Z
				) * (rootPart.CFrame - rootPart.CFrame.Position)
			end
		end

		if rootPart and rootPart.Parent then
			rootPart.CFrame = CFrame.new(
				rootPart.Position.X,
				originalCFrame.Position.Y,
				rootPart.Position.Z
			) * (rootPart.CFrame - rootPart.CFrame.Position)
		end

		fallBoostActive = false
	end
end)

TeleportTab:AddSection("Credits: Phantasm")

TeleportTab:AddSection("Locations")

TeleportTab:AddButton("Death Counter", "Teleport", function()
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = TeleportAreas["Death Counter"]
	end
end)

TeleportTab:AddButton("Middle", "Teleport", function()
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = TeleportAreas["Middle"]
	end
end)

TeleportTab:AddButton("Arena", "Teleport", function()
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = TeleportAreas["Arena"]
	end
end)

TeleportTab:AddButton("Jail", "Teleport", function()
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = TeleportAreas["Jail"]
	end
end)

TeleportTab:AddButton("Bigger Jail", "Teleport", function()
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = TeleportAreas["Bigger Jail"]
	end
end)

TeleportTab:AddButton("Dark Domain", "Teleport", function()
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = TeleportAreas["Dark Domain"]
	end
end)

TeleportTab:AddSection("Mountain")

TeleportTab:AddButton("Mountain", "Teleport", function()
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = TeleportAreas["Mountain"]
	end
end)

TeleportTab:AddSection("Special")

TeleportTab:AddButton("Void", "Teleport", function()
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("HumanoidRootPart") then
		character.HumanoidRootPart.CFrame = TeleportAreas["Void"]
	end
end)

SillyTab:AddSection("Flip on Anim")

SillyTab:AddToggle("Flip on Anim", function(state)
	flipEnabled = state
end)

SillyTab:AddSection("Fall Damage Boost")

SillyTab:AddToggle("Fall Damage Boost", function(state)
	fallBoostEnabled = state
	if not state then
		fallBoostActive = false
	end
end)

local Camera = workspace.CurrentCamera

local BlenderConfig = {
	OrbitSpeed = 10,
	OrbitDistance = 3
}

local BlenderState = {
	IsOrbiting = false,
	CurrentAngle = 0,
	OriginalCFrame = nil,
	Target = nil,
	Connection = nil
}

local blenderEnabled = false
local blenderPinnedName = nil

local function findBlenderTarget()
	if blenderPinnedName and blenderPinnedName ~= "" then
		local lname = blenderPinnedName:lower()
		for _, player in ipairs(Players:GetPlayers()) do
			if player ~= LocalPlayer and (player.Name:lower() == lname or player.DisplayName:lower() == lname) then
				if player.Character and player.Character:FindFirstChild("HumanoidRootPart") and player.Character:FindFirstChild("Humanoid") and player.Character.Humanoid.Health > 0 then
					return player
				end
			end
		end
		return nil
	end
	return getClosestPlayer()
end

local function getClosestPlayer()
	local closestPlayer = nil
	local shortestDistance = math.huge
	local myCharacter = LocalPlayer.Character
	if not myCharacter or not myCharacter:FindFirstChild("HumanoidRootPart") then return nil end
	local myPosition = myCharacter.HumanoidRootPart.Position
	for _, player in ipairs(Players:GetPlayers()) do
		if player ~= LocalPlayer and player.Character and player.Character:FindFirstChild("HumanoidRootPart") and player.Character:FindFirstChild("Humanoid") and player.Character.Humanoid.Health > 0 then
			local distance = (player.Character.HumanoidRootPart.Position - myPosition).Magnitude
			if distance < shortestDistance then
				shortestDistance = distance
				closestPlayer = player
			end
		end
	end
	return closestPlayer
end

local function stopOrbit()
	if not BlenderState.IsOrbiting then return end
	BlenderState.IsOrbiting = false
	if BlenderState.Connection then
		BlenderState.Connection:Disconnect()
		BlenderState.Connection = nil
	end
	BlenderState.Target = nil
	local character = LocalPlayer.Character
	if character and character:FindFirstChild("Humanoid") then
		Camera.CameraSubject = character.Humanoid
		local rootPart = character:FindFirstChild("HumanoidRootPart")
		if rootPart and BlenderState.OriginalCFrame then
			rootPart.Velocity = Vector3.new(0, 0, 0)
			RunService.Heartbeat:Once(function()
				rootPart.CFrame = BlenderState.OriginalCFrame
			end)
		end
	end
end

local function startOrbit()
	local targetPlayer = findBlenderTarget()
	if not targetPlayer or not targetPlayer.Character then return end
	local character = LocalPlayer.Character
	if not character or not character:FindFirstChild("HumanoidRootPart") or not character:FindFirstChild("Humanoid") then return end
	BlenderState.Target = targetPlayer
	BlenderState.IsOrbiting = true
	BlenderState.OriginalCFrame = character.HumanoidRootPart.CFrame
	BlenderState.CurrentAngle = 0
	BlenderState.Connection = RunService.RenderStepped:Connect(function()
		if not BlenderState.IsOrbiting or not BlenderState.Target or not BlenderState.Target.Character or not BlenderState.Target.Character:FindFirstChild("HumanoidRootPart") or BlenderState.Target.Character.Humanoid.Health <= 0 then
			stopOrbit()
			return
		end
		local localRoot = LocalPlayer.Character.HumanoidRootPart
		local targetRoot = BlenderState.Target.Character.HumanoidRootPart
		local targetHumanoid = BlenderState.Target.Character.Humanoid
		if Camera.CameraSubject ~= targetHumanoid then
			Camera.CameraSubject = targetHumanoid
		end
		BlenderState.CurrentAngle = BlenderState.CurrentAngle + BlenderConfig.OrbitSpeed
		local predictedPosition = targetRoot.Position + targetHumanoid.MoveDirection * (targetRoot.Velocity.Magnitude / 2.75)
		local orbitOffset = CFrame.Angles(0, math.rad(BlenderState.CurrentAngle), 0) * CFrame.new(BlenderConfig.OrbitDistance, 0, 0)
		localRoot.CFrame = CFrame.lookAt(localRoot.Position, Vector3.new(predictedPosition.X, localRoot.Position.Y, predictedPosition.Z))
		task.wait()
		localRoot.CFrame = CFrame.new(predictedPosition.X, targetRoot.Position.Y, predictedPosition.Z) * orbitOffset
	end)
end

task.spawn(function()
	while task.wait(0.5) do
		if not blenderEnabled then
			if BlenderState.IsOrbiting then stopOrbit() end
			continue
		end
		if not BlenderState.IsOrbiting then
			startOrbit()
		end
	end
end)

SillyTab:AddSection("Blender")

SillyTab:AddToggle("Blender", function(state)
	blenderEnabled = state
	if not state then stopOrbit() end
end)

SillyTab:AddSlider("Blender Speed", 1, 30, 10, function(value)
	BlenderConfig.OrbitSpeed = value
end)

SillyTab:AddSlider("Blender Distance", 1, 15, 3, function(value)
	BlenderConfig.OrbitDistance = value
end)

SillyTab:AddInput("Pin Target", "Player name...", function(text)
	blenderPinnedName = text ~= "" and text or nil
	if BlenderState.IsOrbiting then
		stopOrbit()
	end
end)

--[[
local COUNTER_ANIM_IDS = {
	'rbxassetid://12351854556',
	'rbxassetid://15311685628',
	'rbxassetid://15128849047',
}

local ThrownModel = workspace:FindFirstChild('Thrown')
local EnemyThrown = nil
if ThrownModel then
	ThrownModel.Archivable = true
	EnemyThrown = ThrownModel:Clone()
	ThrownModel.Archivable = false
	EnemyThrown:ClearAllChildren()
	EnemyThrown.Name = 'Thrown'
	EnemyThrown.Parent = workspace
end

local function isAnimPlaying(humanoid, animId)
	local id = tostring(animId):match('%d+')
	for _, track in ipairs(humanoid:GetPlayingAnimationTracks()) do
		if track.Animation.AnimationId:match(id) then
			return track
		end
	end
	return nil
end

local function isCountering(humanoid)
	local model = humanoid:FindFirstAncestorWhichIsA('Model')
	if model and model:FindFirstChild('Counter') then return true end
	for _, track in ipairs(humanoid:GetPlayingAnimationTracks()) do
		if table.find(COUNTER_ANIM_IDS, track.Animation.AnimationId) then
			return true
		end
	end
	return false
end

local function isDeathCountering(character)
	return character and character:FindFirstChild('Counter') and true or false
end

local AntiMovesDesync = nil
local _desyncStartTime = nil

RunService.Heartbeat:Connect(function()
	if AntiMovesDesync and AntiMovesDesync.CFrame then
		if not _desyncStartTime then
			_desyncStartTime = tick()
		end
		if tick() - _desyncStartTime > 10 then
			AntiMovesDesync = nil
			_desyncStartTime = nil
			return
		end
		local character = LocalPlayer.Character
		local rootPart = character and character:FindFirstChild('HumanoidRootPart')
		if rootPart then
			rootPart.Velocity = Vector3.new(0, 0, 0)
			rootPart.CFrame = AntiMovesDesync.CFrame
		end
	else
		_desyncStartTime = nil
	end
end)

local AntiMovesConfig = {
	Saitama = {},
	Garou = {},
	Genos = {},
	Tatsumaki = {},
	AtomicSamurai = {},
	Suiryu = {},
	MetalBat = {},
	Sonic = {},
	KJ = {},
	FrozenSoul = {},
	Trashcan = false,
}

local function onEnemyAnimPlayedAntiMoves(enemyPlayer, animTrack)
	local animId = animTrack.Animation.AnimationId

	local myChar = LocalPlayer.Character
	local myRoot = myChar and myChar:FindFirstChild('HumanoidRootPart')
	local myHum = myChar and myChar:FindFirstChildOfClass('Humanoid')
	local enemyChar = enemyPlayer.Character
	local enemyRoot = enemyChar and enemyChar:FindFirstChild('HumanoidRootPart')
	local enemyHum = enemyChar and enemyChar:FindFirstChildOfClass('Humanoid')

	if not (myRoot and myHum and enemyRoot and enemyHum) then return end
	if animTrack.WeightTarget == 0 or animTrack.Speed == 0 then return end

	local function desync()
		AntiMovesDesync = { CFrame = CFrame.new(9e9, 9e9, 9e9) }
	end
	local function stopDesync()
		AntiMovesDesync = nil
	end

	task.spawn(function()
		local ok, err = pcall(function()
		if animId:match('10468665991') and AntiMovesConfig.Saitama['Anti Normal Punch'] then
			local p1 = Instance.new('Part', workspace)
			p1.Anchored = true p1.Size = Vector3.new(12.5, 5, 75) p1.CanCollide = false p1.Transparency = 1
			local p2 = Instance.new('Part', workspace)
			p2.Anchored = true p2.Size = Vector3.new(12.5, 5, 75) p2.CanCollide = false p2.Transparency = 1
			local p3 = Instance.new('Part', workspace)
			p3.Anchored = true p3.Size = Vector3.new(12.5, 5, 75) p3.CanCollide = false p3.Transparency = 1
			local t1, t2, t3 = false, false, false
			local conns = {}
			table.insert(conns, p1.Touched:Connect(function(h) if h == myRoot then t1 = true end end))
			table.insert(conns, p1.TouchEnded:Connect(function(h) if h == myRoot then t1 = false end end))
			table.insert(conns, p2.Touched:Connect(function(h) if h == myRoot then t2 = true end end))
			table.insert(conns, p2.TouchEnded:Connect(function(h) if h == myRoot then t2 = false end end))
			table.insert(conns, p3.Touched:Connect(function(h) if h == myRoot then t3 = true end end))
			table.insert(conns, p3.TouchEnded:Connect(function(h) if h == myRoot then t3 = false end end))
			local start = tick()
			while true do
				p1.CFrame = enemyRoot.CFrame * CFrame.new(6, 0, -p1.Size.Z / 2 + 1.5) * CFrame.Angles(0, math.rad(-5), 0)
				p2.CFrame = enemyRoot.CFrame * CFrame.new(-6, 0, -p2.Size.Z / 2 + 1.5) * CFrame.Angles(0, math.rad(5), 0)
				p3.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p3.Size.Z / 2 + 1.5)
				if (t1 or t2 or t3) and not isCountering(myHum) then
					repeat
						p1.CFrame = enemyRoot.CFrame * CFrame.new(6, 0, -p1.Size.Z / 2 + 1.5) * CFrame.Angles(0, math.rad(-5), 0)
						p2.CFrame = enemyRoot.CFrame * CFrame.new(-6, 0, -p2.Size.Z / 2 + 1.5) * CFrame.Angles(0, math.rad(5), 0)
						p3.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p3.Size.Z / 2 + 1.5)
						desync() task.wait()
						if not (t1 or t2 or t3) or tick() >= start + 0.8 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 0.8 or not animTrack.IsPlaying then
					stopDesync() p1:Destroy() p2:Destroy() p3:Destroy()
					for _, c in ipairs(conns) do c:Disconnect() end
					break
				end
			end
		end

		if animId:match('10466974800') and AntiMovesConfig.Saitama['Anti Consecutive Punches'] then
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(12.5, 5, 12.5) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 1.5 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 1.5 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('10471336737') and AntiMovesConfig.Saitama['Anti Shove'] then
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(7.5, 5, 7.5) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 0.5 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 0.5 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('12510170988') and AntiMovesConfig.Saitama['Anti Uppercut'] then
			task.wait(0.25)
			if not animTrack.IsPlaying then return end
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(10, 10, 10) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 0.5 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 0.5 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('11343318134') and AntiMovesConfig.Saitama['Anti Death Counter'] then
			task.wait(7.5)
			local p1 = Instance.new('Part', workspace)
			p1.Anchored = true p1.Size = Vector3.new(125, 5, 500) p1.CanCollide = false p1.Transparency = 1
			local p2 = Instance.new('Part', workspace)
			p2.Anchored = true p2.Size = Vector3.new(125, 5, 500) p2.CanCollide = false p2.Transparency = 1
			local p3 = Instance.new('Part', workspace)
			p3.Anchored = true p3.Size = Vector3.new(125, 5, 500) p3.CanCollide = false p3.Transparency = 1
			local t1, t2, t3 = false, false, false
			local conns = {}
			table.insert(conns, p1.Touched:Connect(function(h) if h == myRoot then t1 = true end end))
			table.insert(conns, p1.TouchEnded:Connect(function(h) if h == myRoot then t1 = false end end))
			table.insert(conns, p2.Touched:Connect(function(h) if h == myRoot then t2 = true end end))
			table.insert(conns, p2.TouchEnded:Connect(function(h) if h == myRoot then t2 = false end end))
			table.insert(conns, p3.Touched:Connect(function(h) if h == myRoot then t3 = true end end))
			table.insert(conns, p3.TouchEnded:Connect(function(h) if h == myRoot then t3 = false end end))
			local start = tick()
			while true do
				p1.CFrame = enemyRoot.CFrame * CFrame.new(60, 0, -p1.Size.Z / 2 + 1.5) * CFrame.Angles(0, math.rad(-15), 0)
				p2.CFrame = enemyRoot.CFrame * CFrame.new(-60, 0, -p2.Size.Z / 2 + 1.5) * CFrame.Angles(0, math.rad(15), 0)
				p3.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p3.Size.Z / 2 + 1.5)
				if t1 or t2 or t3 then
					repeat
						p1.CFrame = enemyRoot.CFrame * CFrame.new(60, 0, -p1.Size.Z / 2 + 1.5) * CFrame.Angles(0, math.rad(-15), 0)
						p2.CFrame = enemyRoot.CFrame * CFrame.new(-60, 0, -p2.Size.Z / 2 + 1.5) * CFrame.Angles(0, math.rad(15), 0)
						p3.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p3.Size.Z / 2 + 1.5)
						desync() task.wait()
						if not (t1 or t2 or t3) or tick() >= start + 2.5 or not animTrack.IsPlaying then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 2.5 or not animTrack.IsPlaying then
					stopDesync() p1:Destroy() p2:Destroy() p3:Destroy()
					for _, c in ipairs(conns) do c:Disconnect() end
					break
				end
			end
		end

		if animId:match('11365563255') and AntiMovesConfig.Saitama['Anti Table Flip'] then
			task.delay(1, function()
				if myChar:FindFirstChild('AbsoluteImmortal', true) and myChar:FindFirstChild('Freeze') then
					task.wait(3)
					if not AntiMovesConfig.Saitama['Anti Table Flip'] then return end
					local start = tick()
					repeat desync() task.wait()
						if tick() >= start + 2.5 then stopDesync() break end
					until false
				end
			end)
		end

		if animId:match('12983333733') and AntiMovesConfig.Saitama['Anti Serious Punch'] then
			task.delay(1, function()
				if myChar:FindFirstChild('AbsoluteImmortal', true) and myChar:FindFirstChild('Freeze') then
					task.wait(4.25)
					if not AntiMovesConfig.Saitama['Anti Serious Punch'] then return end
					local start = tick()
					repeat desync() task.wait()
						if tick() >= start + 2 then stopDesync() break end
					until false
				end
			end)
		end

		if animId:match('13927612951') and AntiMovesConfig.Saitama['Anti Omni-Directional Punch'] then
			if not AntiMovesConfig.Saitama['Anti Omni-Directional Punch'] then return end
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 150 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 150 or tick() >= start + 2.5 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 2.5 then stopDesync() break end
			end
		end

		if animId:match('12272894215') and AntiMovesConfig.Garou['Anti Flowing Water'] then
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(10, 5, 10) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 0.5 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 0.5 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('12273188754') and AntiMovesConfig.Garou['Anti Flowing Water'] then
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(15, 5, 15) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 2 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 2 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('14374357351') and AntiMovesConfig.Garou['Anti Flowing Water'] then
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(10, 5, 15) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 1.5 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 1.5 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect()
					task.wait(0.5)
					local start2 = tick()
					while true do
						if (myRoot.Position - enemyRoot.Position).Magnitude <= 25 then
							repeat desync() task.wait()
								if (myRoot.Position - enemyRoot.Position).Magnitude > 25 or tick() >= start + 2.75 then stopDesync() break end
							until false
						end
						task.wait()
						if tick() >= start + 2.75 then stopDesync() break end
					end
					break
				end
			end
		end

		if animId:match('12296882427') and AntiMovesConfig.Garou['Anti Lethal Whirlwind Stream'] then
			local start = tick()
			while true do
				if (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -2.5)).Position).Magnitude <= 10 and not isCountering(myHum) then
					repeat desync() task.wait()
						if (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -2.5)).Position).Magnitude > 10 or tick() >= start + 0.5 or isCountering(myHum) then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 0.5 then stopDesync() break end
			end
		end

		if animId:match('12296113986') and AntiMovesConfig.Garou['Anti Lethal Whirlwind Stream'] then
			task.delay(1.35, function()
				local start = tick()
				while (myRoot.Position - enemyRoot.Position).Magnitude > 15 do
					task.wait()
					if tick() >= start + 0.65 then stopDesync() return end
				end
				repeat desync() task.wait()
					if (myRoot.Position - enemyRoot.Position).Magnitude > 15 or tick() >= start + 0.65 then stopDesync() break end
				until false
			end)
			local start = tick()
			repeat desync() task.wait()
				if tick() >= start + 0.5 then stopDesync() break end
			until false
		end

		if animId:match('14798608838') and AntiMovesConfig.Garou['Anti Lethal Whirlwind Stream'] then
			task.delay(0.75, function()
				local start = tick()
				while (myRoot.Position - enemyRoot.Position).Magnitude > 25 do
					task.wait()
					if tick() >= start + 0.75 then stopDesync() return end
				end
				repeat desync() task.wait()
					if (myRoot.Position - enemyRoot.Position).Magnitude > 25 or tick() >= start + 0.75 then stopDesync() break end
				until false
			end)
		end

		if animId:match('12307656616') and AntiMovesConfig.Garou['Anti Hunters Grasp'] then
			local start = tick()
			while true do
				if (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -2.5)).Position).Magnitude <= 10 and not isCountering(myHum) then
					repeat desync() task.wait()
						if (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -2.5)).Position).Magnitude > 10 or tick() >= start + 0.35 or isCountering(myHum) then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 0.35 then stopDesync() break end
			end
		end

		if animId:match('13603396939') and AntiMovesConfig.Garou['Anti Preys Peril'] then
			local start = tick()
			while true do
				if (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -1)).Position).Magnitude <= 7.5 then
					if not isCountering(myHum) then
						repeat desync() task.wait()
							if isCountering(myHum) or (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -1)).Position).Magnitude > 7.5 or tick() >= start + 2.5 then stopDesync() break end
						until false
					end
				end
				task.wait()
				if tick() >= start + 2.75 then stopDesync() break end
			end
		end

		if animId:match('16515850153') and AntiMovesConfig.Tatsumaki['Anti Windstorm Fury'] then
			task.spawn(function()
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 15 then
					desync()
				end
				if EnemyThrown then
					local dotted = EnemyThrown:WaitForChild('Dotted', 1)
					if dotted then
						local dots = dotted:WaitForChild('Dots', 1)
						if not dots then return end
						local start = tick()
						while true do
							if (myRoot.Position - dots.Position).Magnitude <= 20 and not isDeathCountering(myChar) then
								repeat desync() task.wait()
									if (myRoot.Position - dots.Position).Magnitude > 20 or tick() >= start + 4.25 or isDeathCountering(myChar) then stopDesync() break end
								until false
							end
							task.wait()
							if tick() >= start + 4.25 then stopDesync() break end
						end
					else
						stopDesync()
					end
				end
			end)
		end

		if animId:match('16431491215') and AntiMovesConfig.Tatsumaki['Anti Stone Grave'] then
			task.spawn(function()
				local start = tick()
				while (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -25)).Position).Magnitude > 25 or isCountering(myHum) do
					task.wait()
					if tick() >= start + 0.75 then stopDesync() return end
				end
				repeat desync() task.wait()
					if (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -20)).Position).Magnitude > 25 or tick() >= start + 0.75 or isCountering(myHum) then stopDesync() break end
				until false
			end)
		end

		if animId:match('16597912086') and AntiMovesConfig.Tatsumaki['Anti Expulsive Push'] then
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 15 and not isCountering(myHum) then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 15 or tick() >= start + 0.75 or isCountering(myHum) then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 0.75 then stopDesync() break end
			end
		end

		if animId:match('16734584478') and AntiMovesConfig.Tatsumaki['Anti Tatsumaki Ult'] then
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 75 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 75 or tick() >= start + 5.75 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 5.75 then stopDesync() break end
			end
		end

		if animId:match('17275150809') and AntiMovesConfig.Tatsumaki['Anti Terrible Tornado'] then
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 50 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 50 or tick() >= start + 1 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 1 then stopDesync() break end
			end
		end

		if animId:match('17278415853') and enemyChar:GetAttribute('Character') == 'Esper' and AntiMovesConfig.Tatsumaki['Anti Terrible Tornado'] then
			task.wait(11)
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 100 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 100 or tick() >= start + 6 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 6 then stopDesync() break end
			end
		end

		if animId:match('13813955149') and AntiMovesConfig.Trashcan then
			if (myRoot.Position - enemyRoot.Position).Magnitude <= 25 then
				desync()
				task.wait(0.75)
				stopDesync()
			end
			if EnemyThrown then
				local conn
				conn = EnemyThrown.ChildAdded:Connect(function(child)
					if child:IsA('MeshPart') and child.Name:lower() == 'trash can' then
						conn:Disconnect()
						local start = tick()
						while true do
							if (myRoot.Position - child.Position).Magnitude <= 25 then
								repeat desync() task.wait()
									if (myRoot.Position - child.Position).Magnitude > 25 or tick() >= start + 2 then stopDesync() break end
								until false
							end
							task.wait()
							if tick() >= start + 2 then stopDesync() break end
						end
					end
				end)
			end
		end

		if animId:match('14719290328') and AntiMovesConfig.MetalBat['Anti Savage Tornado'] then
			if (myRoot.Position - enemyRoot.Position).Magnitude <= 50 then desync() end
			task.wait(0.5)
			if animTrack.IsPlaying then
				local start = tick()
				while true do
					if (myRoot.Position - enemyRoot.Position).Magnitude <= 50 and not isDeathCountering(myChar) then
						repeat desync() task.wait()
							if (myRoot.Position - enemyRoot.Position).Magnitude > 50 or tick() >= start + 3.5 or isDeathCountering(myChar) then stopDesync() break end
						until false
					end
					task.wait()
					if tick() >= start + 3.5 then stopDesync() break end
				end
			else
				stopDesync()
			end
		end

		if animId:match('15128849047') and AntiMovesConfig.MetalBat['Anti Death Blow'] then
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 100 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 100 or isAnimPlaying(enemyHum, '15123665491') or tick() >= start + 3 then stopDesync() break end
					until false
				end
				task.wait()
				if isAnimPlaying(enemyHum, '15123665491') or tick() >= start + 3 then stopDesync() break end
			end
		end

		if animId:match('13376869471') and AntiMovesConfig.Sonic['Anti Flash Strike'] then
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(10, 7.5, 60) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 0.8 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 0.8 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('13294790250') and AntiMovesConfig.Sonic['Anti Whirlwind Kick'] then
			task.wait(0.5)
			local start = tick()
			while true do
				if (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -2.5)).Position).Magnitude <= 10 and not isCountering(myHum) then
					repeat desync() task.wait()
						if (myRoot.Position - (enemyRoot.CFrame * CFrame.new(0, 0, -2.5)).Position).Magnitude > 10 or tick() >= start + 0.75 or isCountering(myHum) then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 0.75 then stopDesync() break end
			end
		end

		if animId:match('13632347366') and AntiMovesConfig.Sonic['Anti Twinblade Rush'] then
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 75 and not isDeathCountering(myChar) then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 75 or not animTrack.IsPlaying or tick() >= start + 1.75 or isDeathCountering(myChar) then stopDesync() break end
					until false
				end
				task.wait()
				if not animTrack.IsPlaying or tick() >= start + 1.75 then stopDesync() break end
			end
		end

		if animId:match('13881335713') and AntiMovesConfig.Sonic['Anti Fourfold Flashstrike'] then
			task.wait(0.75)
			if not animTrack.IsPlaying then return end
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(35, 5, 60) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isDeathCountering(myChar) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 0.75 or not animTrack.IsPlaying or isDeathCountering(myChar) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 0.75 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('13723174078') and AntiMovesConfig.Sonic['Anti Carnage'] then
			task.wait(0.5)
			if not animTrack.IsPlaying then return end
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(35, 50, 250) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, -p.Size.Y / 2, -p.Size.Z / 2)
				if hit and not isDeathCountering(myChar) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 2.5 or not animTrack.IsPlaying or isDeathCountering(myChar) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 2.5 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('14721837245') and AntiMovesConfig.Genos['Anti Thunder Kick'] then
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 25 and not isCountering(myHum) then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 25 or not animTrack.IsPlaying or tick() >= start + 1.5 or isCountering(myHum) then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 1.5 then
					stopDesync()
					task.wait(1)
					local start2 = tick()
					while true do
						if (myRoot.Position - enemyRoot.Position).Magnitude <= 100 then
							repeat desync() task.wait()
								if (myRoot.Position - enemyRoot.Position).Magnitude > 100 or not animTrack.IsPlaying or tick() >= start2 + 1.5 then stopDesync() break end
							until false
						end
						task.wait()
						if tick() >= start2 + 1.5 then stopDesync() break end
					end
					break
				end
			end
		end

		if animId:match('13083332742') and AntiMovesConfig.Genos['Anti Flamewave Cannon'] then
			task.wait(1)
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(12.5, 5, 1000) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			task.delay(0.25, function() p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2) end)
			local start = tick()
			while true do
				if hit and not isDeathCountering(myChar) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 4 or not animTrack.IsPlaying or isDeathCountering(myChar) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 4 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('13146710762') and AntiMovesConfig.Genos['Anti Incinerate'] then
			task.wait(3.25)
			if not myChar:FindFirstChild('ForceField') then return end
			local p1 = Instance.new('Part', workspace)
			p1.Anchored = true p1.Size = Vector3.new(100, 75, 400) p1.CanCollide = false p1.Transparency = 1
			local p2 = Instance.new('Part', workspace)
			p2.Anchored = true p2.Size = Vector3.new(100, 75, 400) p2.CanCollide = false p2.Transparency = 1
			local p3 = Instance.new('Part', workspace)
			p3.Anchored = true p3.Size = Vector3.new(100, 75, 400) p3.CanCollide = false p3.Transparency = 1
			local t1, t2, t3 = false, false, false
			local conns = {}
			table.insert(conns, p1.Touched:Connect(function(h) if h == myRoot then t1 = true end end))
			table.insert(conns, p1.TouchEnded:Connect(function(h) if h == myRoot then t1 = false end end))
			table.insert(conns, p2.Touched:Connect(function(h) if h == myRoot then t2 = true end end))
			table.insert(conns, p2.TouchEnded:Connect(function(h) if h == myRoot then t2 = false end end))
			table.insert(conns, p3.Touched:Connect(function(h) if h == myRoot then t3 = true end end))
			table.insert(conns, p3.TouchEnded:Connect(function(h) if h == myRoot then t3 = false end end))
			p1.CFrame = enemyRoot.CFrame * CFrame.new(50, 0, -p1.Size.Z / 2 + 2.5) * CFrame.Angles(0, math.rad(-15), 0)
			p2.CFrame = enemyRoot.CFrame * CFrame.new(-50, 0, -p2.Size.Z / 2 + 2.5) * CFrame.Angles(0, math.rad(15), 0)
			p3.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p3.Size.Z / 2 + 2.5)
			local start = tick()
			while true do
				if (t1 or t2 or t3) and not isDeathCountering(myChar) then
					repeat desync() task.wait()
						if not (t1 or t2 or t3) or tick() >= start + 6 or isDeathCountering(myChar) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 6 or not animTrack.IsPlaying then
					stopDesync() p1:Destroy() p2:Destroy() p3:Destroy()
					for _, c in ipairs(conns) do c:Disconnect() end
					break
				end
			end
		end

		if animId:match('15391323441') and AntiMovesConfig.AtomicSamurai['Anti Atomic Samurai Ult'] then
			task.wait(5.5)
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 125 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 125 or tick() >= start + 1 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 1 then stopDesync() break end
			end
		end

		if animId:match('15520132233') and AntiMovesConfig.AtomicSamurai['Anti Sunset'] then
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 50 and not isDeathCountering(myChar) then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 50 or tick() >= start + 3.3 or not animTrack.IsPlaying or isDeathCountering(myChar) then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 3.3 or not animTrack.IsPlaying then
					stopDesync()
					repeat task.wait() until tick() >= start + 5.5
					while true do
						if (myRoot.Position - enemyRoot.Position).Magnitude <= 100 and not isDeathCountering(myChar) then
							repeat desync() task.wait()
								if (myRoot.Position - enemyRoot.Position).Magnitude > 100 or tick() >= start + 6.5 or not animTrack.IsPlaying or isDeathCountering(myChar) then stopDesync() break end
							until false
						end
						task.wait()
						if tick() >= start + 6.5 or not animTrack.IsPlaying then stopDesync() break end
					end
					break
				end
			end
		end

		if animId:match('15676072469') and AntiMovesConfig.AtomicSamurai['Anti Solar Cleave'] then
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(50, 10, 150) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isDeathCountering(myChar) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 2 or not animTrack.IsPlaying or isDeathCountering(myChar) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 2 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('16082123712') and AntiMovesConfig.AtomicSamurai['Anti Atomic Slash'] then
			task.wait(2.5)
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 50 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 50 or tick() >= start + 1.5 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 1.5 then stopDesync() break end
			end
		end

		if animId:match('16057411888') and AntiMovesConfig.AtomicSamurai['Anti Atomic Slash Finisher'] then
			task.wait(4.25)
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 50 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 50 or tick() >= start + 2 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 2 then stopDesync() break end
			end
		end

		if animId:match('17857788598') and AntiMovesConfig.Suiryu['Anti Whirlwind Drop'] then
			task.wait(0.65)
			if not animTrack.IsPlaying then return end
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(35, 2048, 35) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 0.85 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 0.85 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('18435535291') and AntiMovesConfig.Suiryu['Anti Suiryu Ult'] then
			task.wait(4.25)
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 100 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 100 or tick() >= start + 1.25 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 1.25 then stopDesync() break end
			end
		end

		if animId:match('129651400898906') and AntiMovesConfig.Suiryu['Anti Grand Fissure'] then
			task.wait(0.5)
			local frozenCFrame = enemyRoot.CFrame
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 75 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 75 or tick() >= start + 1.25 or not animTrack.IsPlaying then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 1.25 or not animTrack.IsPlaying then
					stopDesync()
					task.wait(1)
					while true do
						if (myRoot.Position - frozenCFrame.Position).Magnitude <= 75 then
							repeat desync() task.wait()
								if (myRoot.Position - frozenCFrame.Position).Magnitude > 75 or tick() >= start + 3 then stopDesync() break end
							until false
						end
						task.wait()
						if tick() >= start + 3 then stopDesync() break end
					end
					break
				end
			end
		end

		if animId:match('18896229321') and AntiMovesConfig.Suiryu['Anti Twin Fangs'] then
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 15 and not isCountering(myHum) then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 15 or tick() >= start + 3.5 or not animTrack.IsPlaying or isCountering(myHum) then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 3.5 or not animTrack.IsPlaying then
					stopDesync()
					task.wait(1)
					if not animTrack.IsPlaying then return end
					if (myRoot.Position - enemyRoot.Position).Magnitude <= 25 then
						repeat desync() task.wait()
							if (myRoot.Position - enemyRoot.Position).Magnitude > 25 or tick() >= start + 5.5 or not animTrack.IsPlaying then stopDesync() break end
						until false
					end
					break
				end
			end
		end

		if animId:match('18897119503') and AntiMovesConfig.Suiryu['Anti Earth Splitting Strike'] then
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(35, 10, 75) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit then
					repeat desync() task.wait()
						if not hit or tick() >= start + 2.5 or not animTrack.IsPlaying then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 2.5 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('106755459092436') and AntiMovesConfig.Suiryu['Anti Last Breath'] then
			task.wait(3)
			if not (isAnimPlaying(enemyHum, '106755459092436') or isAnimPlaying(enemyHum, '132259592388175')) then return end
			local start = tick()
			while true do
				if isAnimPlaying(enemyHum, '106755459092436') or isAnimPlaying(enemyHum, '132259592388175') then
					repeat desync() task.wait()
					until tick() >= start + 3.5 or not (isAnimPlaying(enemyHum, '106755459092436') or isAnimPlaying(enemyHum, '132259592388175'))
					stopDesync()
				end
				task.wait()
				if tick() >= start + 3.5 then stopDesync() break end
			end
		end

		if animId:match('75502010126640') and AntiMovesConfig.Suiryu['Anti Last Breath'] then
			task.wait(10)
			local start = tick()
			while true do
				if (myRoot.Position - enemyRoot.Position).Magnitude <= 100 then
					repeat desync() task.wait()
						if (myRoot.Position - enemyRoot.Position).Magnitude > 100 or tick() >= start + 3 then stopDesync() break end
					until false
				end
				task.wait()
				if tick() >= start + 3 then stopDesync() break end
			end
		end

		if animId:match('17141153099') and AntiMovesConfig.KJ['Anti Stoic Bomb'] then
			task.delay(2, function()
				local start = tick()
				while (myRoot.Position - enemyRoot.Position).Magnitude > 75 do
					task.wait()
					if tick() >= start + 1.5 then stopDesync() return end
				end
				repeat desync() task.wait()
					if (myRoot.Position - enemyRoot.Position).Magnitude > 75 or tick() >= start + 1.5 then stopDesync() break end
				until false
			end)
		end

		if animId:match('17354976067') and AntiMovesConfig.KJ['Anti 20-20-20 Dropkick'] then
			task.delay(1, function()
				local p = Instance.new('Part', workspace)
				p.Anchored = true p.Size = Vector3.new(25, 5, 125) p.CanCollide = false p.Transparency = 1
				local hit = false
				local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
				local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
				local start = tick()
				while true do
					p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Y / 2)
					if hit then break end
					RunService.RenderStepped:Wait()
					if tick() >= start + 5 or not animTrack.IsPlaying then
						stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() return
					end
				end
				repeat desync() task.wait()
					if not hit or tick() >= start + 5 or not animTrack.IsPlaying then stopDesync() break end
				until false
				p:Destroy() c1:Disconnect() c2:Disconnect()
			end)
		end

		if animId:match('18462894593') and AntiMovesConfig.KJ['Anti Five Seasons'] then
			task.delay(6.75, function()
				local start = tick()
				repeat desync() task.wait()
					if tick() >= start + 1 then stopDesync() return end
				until false
			end)
		end

		if animId:match('100558589307006') and AntiMovesConfig.FrozenSoul['Anti Permafrost'] then
			task.wait(0.35)
			if not animTrack.IsPlaying then return end
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(45, 25, 85) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 0.65 or not animTrack.IsPlaying then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 0.65 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('137561511768861') and AntiMovesConfig.FrozenSoul['Anti Frost Forge'] then
			task.delay(1, function()
				local start = tick()
				while (myRoot.Position - enemyRoot.Position).Magnitude > 150 do
					task.wait()
					if tick() >= start + 0.75 then stopDesync() return end
				end
				repeat desync() task.wait()
					if (myRoot.Position - enemyRoot.Position).Magnitude > 150 or tick() >= start + 0.75 then stopDesync() break end
				until false
			end)
		end

		if animId:match('112620365240235') and AntiMovesConfig.FrozenSoul['Anti Freezing Path'] then
			task.wait(0.5)
			if not animTrack.IsPlaying then return end
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(20, 10, 35) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 4 or not animTrack.IsPlaying then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 4 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end

		if animId:match('75547590335774') and AntiMovesConfig.FrozenSoul['Anti Judgement Chain'] then
			task.wait(0.35)
			if not animTrack.IsPlaying then return end
			local p = Instance.new('Part', workspace)
			p.Anchored = true p.Size = Vector3.new(10, 5, 175) p.CanCollide = false p.Transparency = 1
			local hit = false
			local c1 = p.Touched:Connect(function(h) if h == myRoot then hit = true end end)
			local c2 = p.TouchEnded:Connect(function(h) if h == myRoot then hit = false end end)
			local start = tick()
			while true do
				p.CFrame = enemyRoot.CFrame * CFrame.new(0, 0, -p.Size.Z / 2)
				if hit and not isCountering(myHum) then
					repeat desync() task.wait()
						if not hit or tick() >= start + 1 or not animTrack.IsPlaying then stopDesync() break end
					until false
				end
				RunService.RenderStepped:Wait()
				if tick() >= start + 1 or not animTrack.IsPlaying then
					stopDesync() p:Destroy() c1:Disconnect() c2:Disconnect() break
				end
			end
		end
	end)
		if not ok then
			AntiMovesDesync = nil
		end
	end)
end

local function setupAntiMovesEnemy(player)
	if player == LocalPlayer then return end
	local function onCharAdded(char)
		local humanoid = char:WaitForChild('Humanoid', 5)
		if not humanoid then return end
		humanoid.AnimationPlayed:Connect(function(track)
			onEnemyAnimPlayedAntiMoves(player, track)
		end)
	end
	if player.Character then task.spawn(onCharAdded, player.Character) end
	player.CharacterAdded:Connect(onCharAdded)
end

for _, player in ipairs(Players:GetPlayers()) do
	setupAntiMovesEnemy(player)
end
Players.PlayerAdded:Connect(setupAntiMovesEnemy)
]]

AntiSkillsTab:AddSection("Anti Moves")

local _antiMovesMultiRefs = {}

AntiSkillsTab:AddToggle("Enable All Anti Moves", function(state)
	AntiMovesConfig.Trashcan = state
	for _, ref in ipairs(_antiMovesMultiRefs) do
		ref:SetAll(state)
	end
end)

AntiSkillsTab:AddToggle("Anti Trash Can", function(state)
	AntiMovesConfig.Trashcan = state
end)

AntiSkillsTab:AddSection("Saitama")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Saitama Moves", {
	"Anti Normal Punch",
	"Anti Consecutive Punches",
	"Anti Shove",
	"Anti Uppercut",
	"Anti Death Counter",
	"Anti Table Flip",
	"Anti Serious Punch",
	"Anti Omni-Directional Punch",
}, function(selected)
	AntiMovesConfig.Saitama = selected
end))

AntiSkillsTab:AddSection("Garou")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Garou Moves", {
	"Anti Flowing Water",
	"Anti Lethal Whirlwind Stream",
	"Anti Hunters Grasp",
	"Anti Preys Peril",
}, function(selected)
	AntiMovesConfig.Garou = selected
end))

AntiSkillsTab:AddSection("Genos")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Genos Moves", {
	"Anti Thunder Kick",
	"Anti Flamewave Cannon",
	"Anti Incinerate",
}, function(selected)
	AntiMovesConfig.Genos = selected
end))

AntiSkillsTab:AddSection("Tatsumaki")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Tatsumaki Moves", {
	"Anti Windstorm Fury",
	"Anti Stone Grave",
	"Anti Expulsive Push",
	"Anti Tatsumaki Ult",
	"Anti Terrible Tornado",
}, function(selected)
	AntiMovesConfig.Tatsumaki = selected
end))

AntiSkillsTab:AddSection("Atomic Samurai")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Atomic Samurai Moves", {
	"Anti Atomic Samurai Ult",
	"Anti Sunset",
	"Anti Solar Cleave",
	"Anti Atomic Slash",
	"Anti Atomic Slash Finisher",
}, function(selected)
	AntiMovesConfig.AtomicSamurai = selected
end))

AntiSkillsTab:AddSection("Suiryu")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Suiryu Moves", {
	"Anti Whirlwind Drop",
	"Anti Suiryu Ult",
	"Anti Grand Fissure",
	"Anti Twin Fangs",
	"Anti Earth Splitting Strike",
	"Anti Last Breath",
}, function(selected)
	AntiMovesConfig.Suiryu = selected
end))

AntiSkillsTab:AddSection("Metal Bat")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Metal Bat Moves", {
	"Anti Savage Tornado",
	"Anti Death Blow",
}, function(selected)
	AntiMovesConfig.MetalBat = selected
end))

AntiSkillsTab:AddSection("Sonic")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Sonic Moves", {
	"Anti Flash Strike",
	"Anti Whirlwind Kick",
	"Anti Twinblade Rush",
	"Anti Carnage",
	"Anti Fourfold Flashstrike",
}, function(selected)
	AntiMovesConfig.Sonic = selected
end))

AntiSkillsTab:AddSection("KJ")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("KJ Moves", {
	"Anti Stoic Bomb",
	"Anti 20-20-20 Dropkick",
	"Anti Five Seasons",
}, function(selected)
	AntiMovesConfig.KJ = selected
end))

AntiSkillsTab:AddSection("Frozen Soul")
table.insert(_antiMovesMultiRefs, AntiSkillsTab:AddMultiToggle("Frozen Soul Moves", {
	"Anti Permafrost",
	"Anti Frost Forge",
	"Anti Freezing Path",
	"Anti Judgement Chain",
}, function(selected)
	AntiMovesConfig.FrozenSoul = selected
end))

AntiSkillsTab:AddSection("Anti Counters")

local antiDeathCounterEnabled = false

local function antiDCFixCam()
	local character = LocalPlayer.Character
	if not character then return end
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if humanoid and workspace.CurrentCamera then
		local currentCFrame = workspace.CurrentCamera.CFrame
		workspace.CurrentCamera:Destroy()
		local newCamera = Instance.new("Camera", workspace)
		newCamera.CameraType = Enum.CameraType.Custom
		newCamera.CameraSubject = humanoid
		newCamera.CFrame = currentCFrame
		LocalPlayer.CameraMode = Enum.CameraMode.Classic
		local head = character:FindFirstChild("Head")
		if head then head.Anchored = false end
	end
end

local function onAntiDCAnimPlayed(animationTrack)
	if not antiDeathCounterEnabled then return end
	if not animationTrack.Animation.AnimationId:match("11343250001") then return end

	local myCharacter = LocalPlayer.Character
	local myRoot = myCharacter and myCharacter:FindFirstChild("HumanoidRootPart")
	local myHumanoid = myCharacter and myCharacter:FindFirstChildOfClass("Humanoid")
	if not myCharacter or not myRoot or not myHumanoid then return end

	animationTrack:Stop()
	task.spawn(antiDCFixCam)

	myCharacter:WaitForChild("AbsoluteImmortal", 1)
	if not myCharacter:FindFirstChild("AbsoluteImmortal") then return end

	local originalCFrame = myRoot.CFrame
	local targetPlayer = nil

	for _, player in ipairs(Players:GetPlayers()) do
		if player ~= LocalPlayer then
			local targetChar = player.Character
			local targetRoot = targetChar and targetChar:FindFirstChild("HumanoidRootPart")
			local targetHum = targetChar and targetChar:FindFirstChildOfClass("Humanoid")
			if targetChar and targetRoot and targetHum then
				for _, track in ipairs(targetHum:GetPlayingAnimationTracks()) do
					if track.Animation.AnimationId:match("11343318134") and (myRoot.Position - targetRoot.Position).Magnitude <= 15 then
						targetPlayer = player
						break
					end
				end
			end
		end
		if targetPlayer then break end
	end

	local targetHumanoidToWatch
	if targetPlayer then
		local targetChar = targetPlayer.Character
		targetHumanoidToWatch = targetChar and targetChar:FindFirstChildOfClass("Humanoid")
		game:GetService("StarterGui"):SetCore("SendNotification", {
			Title = "Anti Death Counter",
			Text = targetPlayer.DisplayName .. " death countered you!",
			Duration = 5,
		})
	else
		targetHumanoidToWatch = Instance.new("Humanoid")
		targetHumanoidToWatch.Health = 100
		task.delay(2, function() targetHumanoidToWatch.Health = 0 end)
		game:GetService("StarterGui"):SetCore("SendNotification", {
			Title = "Anti Death Counter",
			Text = "Could not find who countered you.",
			Duration = 5,
		})
	end

	local currentCamera = workspace.CurrentCamera
	local originalCameraSubject = currentCamera and currentCamera.CameraSubject or nil
	if currentCamera then currentCamera.CameraSubject = nil end

	local startTime = tick()
	local safeCFrame = CollectAllVoidCFrame

	repeat
		myRoot.CFrame = safeCFrame
		RunService.RenderStepped:Wait()
	until (targetHumanoidToWatch and targetHumanoidToWatch.Health <= 0) or myHumanoid.Health <= 0 or tick() >= startTime + 10

	if currentCamera then currentCamera.CameraSubject = originalCameraSubject end

	myRoot.CFrame = originalCFrame
	task.wait(1)

	local freeze = myCharacter:FindFirstChild("Freeze")
	if freeze then freeze:Destroy() end
	local noRotate = myCharacter:FindFirstChild("NoRotate")
	if noRotate then noRotate:Destroy() end

	task.spawn(antiDCFixCam)
end

local function setupAntiDCCharacter(character)
	local humanoid = character:WaitForChild("Humanoid")
	humanoid.AnimationPlayed:Connect(onAntiDCAnimPlayed)
end

if LocalPlayer.Character then
	task.spawn(setupAntiDCCharacter, LocalPlayer.Character)
end
LocalPlayer.CharacterAdded:Connect(setupAntiDCCharacter)

AntiSkillsTab:AddToggle("Anti Death Counter", function(state)
	antiDeathCounterEnabled = state
end)

local antiDeathBlowEnabled = false
local antiDeathBlowDesync = nil

RunService.Heartbeat:Connect(function()
	if antiDeathBlowDesync and antiDeathBlowDesync.CFrame then
		local character = LocalPlayer.Character
		local rootPart = character and character:FindFirstChild("HumanoidRootPart")
		if rootPart then
			rootPart.Velocity = Vector3.new(0, 0, 0)
			rootPart.CFrame = antiDeathBlowDesync.CFrame
		end
	end
end)

local function onEnemyAnimPlayed(enemyPlayer, animationTrack)
	if not antiDeathBlowEnabled then return end

	local animId = animationTrack.Animation.AnimationId
	local myCharacter = LocalPlayer.Character
	local myRoot = myCharacter and myCharacter:FindFirstChild("HumanoidRootPart")
	local enemyCharacter = enemyPlayer.Character
	local enemyRoot = enemyCharacter and enemyCharacter:FindFirstChild("HumanoidRootPart")

	if not myRoot or not enemyRoot then return end
	if not animId:match("15128849047") then return end
	if (myRoot.Position - enemyRoot.Position).Magnitude > 100 then return end

	game:GetService("StarterGui"):SetCore("SendNotification", {
		Title = "Anti Death Blow",
		Text = "Dodging " .. enemyPlayer.DisplayName .. "'s Death Blow!",
		Duration = 3,
	})

	local startTime = tick()
	local isFinished = false
	local enemyHumanoid = enemyCharacter and enemyCharacter:FindFirstChildOfClass("Humanoid")
	local animConnection

	if enemyHumanoid then
		animConnection = enemyHumanoid.AnimationPlayed:Connect(function(track)
			if track.Animation.AnimationId:match("15123665491") then
				isFinished = true
			end
		end)
	end

	antiDeathBlowDesync = { CFrame = CollectAllVoidCFrame }

	repeat
		task.wait(0.1)
	until isFinished or tick() >= startTime + 3

	antiDeathBlowDesync = nil

	if animConnection then
		animConnection:Disconnect()
	end
end

local function setupAntiDBEnemy(player)
	if player == LocalPlayer then return end
	local function onCharAdded(char)
		local humanoid = char:WaitForChild("Humanoid", 5)
		if not humanoid then return end
		humanoid.AnimationPlayed:Connect(function(track)
			onEnemyAnimPlayed(player, track)
		end)
	end
	if player.Character then task.spawn(onCharAdded, player.Character) end
	player.CharacterAdded:Connect(onCharAdded)
end

for _, player in ipairs(Players:GetPlayers()) do
	setupAntiDBEnemy(player)
end
Players.PlayerAdded:Connect(setupAntiDBEnemy)

AntiSkillsTab:AddToggle("Anti Death Blow", function(state)
	antiDeathBlowEnabled = state
end)
