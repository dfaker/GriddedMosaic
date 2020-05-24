local msg = require('mp.msg')
local assdraw = require('mp.assdraw')

local script_name = "easycrop"

-- Number of crop points currently chosen (0 to 2)
local points = {}
-- True if in cropping selection mode
local cropping = false
-- Original value of osc property
local osc_prop = false

-- Helper that converts two points to top-left and bottom-right
local swizzle_points = function (p1, p2)
    if p1.x > p2.x then p1.x, p2.x = p2.x, p1.x end
    if p1.y > p2.y then p1.y, p2.y = p2.y, p1.y end
end

local clamp = function (val, min, max)
    assert(min <= max)
    if val < min then return min end
    if val > max then return max end
    return val
end

local video_space_from_screen_space = function (ssp)
    -- Video native dimensions and screen size
    local vid_w = mp.get_property("width")
    local vid_h = mp.get_property("height")
    local osd_w = mp.get_property("osd-width")
    local osd_h = mp.get_property("osd-height")

    -- Factor by which the video is scaled to fit the screen
    local scale = math.min(osd_w/vid_w, osd_h/vid_h)

    -- Size video takes up in screen
    local vid_sw, vid_sh = scale*vid_w, scale*vid_h

    -- Video offset within screen
    local off_x = math.floor((osd_w - vid_sw)/2)
    local off_y = math.floor((osd_h - vid_sh)/2)

    local vsp = {}

    -- Move the point to within the video
    vsp.x = clamp(ssp.x, off_x, off_x + vid_sw)
    vsp.y = clamp(ssp.y, off_y, off_y + vid_sh)

    -- Convert screen-space to video-space
    vsp.x = math.floor((vsp.x - off_x) / scale)
    vsp.y = math.floor((vsp.y - off_y) / scale)

    return vsp
end

local screen_space_from_video_space = function (vsp)
    -- Video native dimensions and screen size
    local vid_w = mp.get_property("width")
    local vid_h = mp.get_property("height")
    local osd_w = mp.get_property("osd-width")
    local osd_h = mp.get_property("osd-height")

    -- Factor by which the video is scaled to fit the screen
    local scale = math.min(osd_w/vid_w, osd_h/vid_h)

    -- Size video takes up in screen
    local vid_sw, vid_sh = scale*vid_w, scale*vid_h

    -- Video offset within screen
    local off_x = math.floor((osd_w - vid_sw)/2)
    local off_y = math.floor((osd_h - vid_sh)/2)

    local ssp = {}
    ssp.x = vsp.x * scale + off_x
    ssp.y = vsp.y * scale + off_y
    return ssp
end

-- Wrapper that converts RRGGBB / RRGGBBAA to ASS format
local ass_set_color = function (idx, color)
    assert(color:len() == 8 or color:len() == 6)
    local ass = ""

    -- Set alpha value (if present)
    if color:len() == 8 then
        local alpha = 0xff - tonumber(color:sub(7, 8), 16)
        ass = ass .. string.format("\\%da&H%X&", idx, alpha)
    end

    -- Swizzle RGB to BGR and build ASS string
    color = color:sub(5, 6) .. color:sub(3, 4) .. color:sub(1, 2)
    return "{" .. ass .. string.format("\\%dc&H%s&", idx, color) .. "}"
end

local draw_rect = function (p1, p2)
    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")

    ass = assdraw.ass_new()

    -- Draw overlay over surrounding unselected region

    ass:draw_start()
    ass:pos(0, 0)

    ass:append(ass_set_color(1, "000000aa"))
    ass:append(ass_set_color(3, "00000000"))

    local l = math.min(p1.x, p2.x)
    local r = math.max(p1.x, p2.x)
    local u = math.min(p1.y, p2.y)
    local d = math.max(p1.y, p2.y)

    ass:rect_cw(0, 0, l, osd_h)
    ass:rect_cw(r, 0, osd_w, osd_h)
    ass:rect_cw(l, 0, r, u)
    ass:rect_cw(l, d, r, osd_h)

    local midx = math.floor((r+l)/2)
    local midy = math.floor((u+d)/2)

    ass:rect_cw(midx-2, midy+2, midx+2, midy-2)

    ass:draw_stop()

    -- Draw border around selected region

    ass:new_event()
    ass:draw_start()
    ass:pos(0, 0)

    ass:append(ass_set_color(1, "00000000"))
    ass:append(ass_set_color(3, "000000ff"))
    ass:append("{\\bord2}")

    ass:rect_cw(p1.x, p1.y, p2.x, p2.y)

    ass:draw_stop()

    mp.set_osd_ass(osd_w, osd_h, ass.text)
end

local draw_fill = function ()
    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")

    ass = assdraw.ass_new()
    ass:draw_start()
    ass:pos(0, 0)

    ass:append(ass_set_color(1, "000000aa"))
    ass:append(ass_set_color(3, "00000000"))
    ass:rect_cw(0, 0, osd_w, osd_h)

    ass:draw_stop()
    mp.set_osd_ass(osd_w, osd_h, ass.text)
end

local draw_clear = function ()
    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")
    mp.set_osd_ass(osd_w, osd_h, "")
end

local arl = {1,2,3,4}
local ari = 0
local ar=2.0

local draw_cropper = function ()
    if #points == 1 then
        local p1 = screen_space_from_video_space(points[1])
        local p2 = {}
        p2.x, p2.y = mp.get_mouse_pos()
        --if math.abs( p1.x-p2.x ) > math.abs( p1.y-p2.y ) then
        --    p2.x = p1.x + (math.abs( p1.y-p2.y )*ar)
        --else
        --    p2.y = p1.y + (math.abs( p1.x-p2.x )*ar)
        --end
        draw_rect(p1, p2)
    end
end

local uncrop = function ()
    mp.command("no-osd vf del @" .. script_name .. ":crop")

    mp.command(string.format("script-message easycrop %s %s %s %s", 0, 0, 0, 0) )
    msg.warn(string.format("script-message easycrop %s %s %s %s", 0, 0, 0, 0) )
end

local crop = function(p1, p2)
    swizzle_points(p1, p2)
    --if math.abs( p1.x-p2.x ) > math.abs( p1.y-p2.y ) then
    --    p2.x = p1.x + (math.abs( p1.y-p2.y )*ar)
    --else
    --    p2.y = p1.y + (math.abs( p1.x-p2.x )*ar)
    --end
    local w = p2.x - p1.x
    local h = p2.y - p1.y

    mp.command(string.format("script-message easycrop %s %s %s %s", w, h, p1.x, p1.y) )
    msg.warn(string.format("script-message easycrop coords %s %s %s %s", w, h, p1.x, p1.y))

    local ok, err = mp.command(string.format(
        "no-osd vf add @%s:crop=%s:%s:%s:%s", script_name, w, h, p1.x, p1.y))



    if not ok then
        mp.osd_message("Cropping failed")
        points = {}
    end
end

local easycrop_stop = function ()
    mp.set_property("osc", osc_prop)
    cropping = false
    mp.remove_key_binding("easycrop_mouse_btn0")
    draw_clear()
end

local mouse_btn0_cb = function ()
    if not cropping then
        return
    end

    local mx, my = mp.get_mouse_pos()
    table.insert(points, video_space_from_screen_space({ x = mx, y = my }))

    if #points == 2 then
        crop(points[1], points[2])
        easycrop_stop()
    end
end

local easycrop_start = function ()
    -- Cropping requires swdec or hwdec with copy-back
    local hwdec = mp.get_property("hwdec-current")
    if hwdec == nil then
        return mp.msg.error("Cannot determine current hardware decoder mode")
    end
    -- Check whitelist of ok values
    local valid_hwdec = {
       ["no"] = true, -- software decoding
       -- Taken from mpv manual
       ["videotoolbox-co"] = true,
       ["vaapi-copy"] = true,
       ["dxva2-copy"] = true,
       ["d3d11va-copy"] = true,
       ["mediacodec"] = true
    }
    if not valid_hwdec[hwdec] then
        return mp.osd_message("Cropping requires swdec or hwdec with copy-back (see mpv manual)")
    end

    -- Just clear the current crop and return, if there is one
    if #points ~= 0 then
        uncrop()
        points = {}
        return
    end

    -- Hide OSC
    osc_prop = mp.get_property("osc")
    mp.set_property("osc", "no")

    cropping = true
    mp.add_forced_key_binding("mouse_btn0", "easycrop_mouse_btn0", mouse_btn0_cb)
    draw_fill()
end

local easycrop_activate = function ()

    
    
    if cropping then
        easycrop_stop()
    else
        easycrop_start()
    end
end

local incrementAR = function()
    ari = (ari+1) % ((#arl))
    mp.osd_message(arl[ari+1])
    ar = arl[ari+1]
end

local decrementAR = function()
    ari = (ari-1) % ((#arl))
    mp.osd_message(arl[ari+1])
    ar = arl[ari+1]
end


require 'mp.options'
local options = {
    windowWidth = 12,
    postMoveOffset=1
}
read_options(options, "easyCrop")

local windowWidth = options['windowWidth']
local postMoveOffset = options['postMoveOffset']
local windowCentre = windowWidth/2

local moveWindow = function(increment)
    if windowCentre<(windowWidth/2) then
        windowCentre = (windowWidth/2)
    end
    local duration = mp.get_property('duration')
    if windowCentre> duration-(windowWidth/2) then
        windowCentre = duration-(windowWidth/2)
    end
    windowCentre = windowCentre + increment
    mp.set_property("ab-loop-a", windowCentre-(windowWidth/2))
    mp.set_property("ab-loop-b", windowCentre+(windowWidth/2))
    mp.set_property("start", windowCentre-(windowWidth/2))
    mp.set_property("end", windowCentre+(windowWidth/2))
    mp.set_property("speed",  windowWidth/4 )
    mp.command(string.format("seek %s absolute exact", windowCentre+(windowWidth/2)-postMoveOffset ) )
end

local moveWindowForwards = function()
    moveWindow(0.1)
end

local moveWindowBackwards = function()
    moveWindow(-0.1)
end

local fastmoveWindowForwards = function()
    moveWindow(5)
end

local fastmoveWindowBackwards = function()
    moveWindow(-5)
end

local superfastmoveWindowForwards = function()
    moveWindow(windowWidth*10)
end

local superfastmoveWindowBackwards = function()
    moveWindow(-windowWidth*10)
end

local exportCurrentRange  = function()
    msg.warn(string.format("script-message easycrop range %s %s %s", windowCentre-(windowWidth/2),windowCentre+(windowWidth/2),windowWidth ))
    if #points ~= 0 then
        uncrop()
        points = {}
    end
end

mp.add_forced_key_binding("y", exportCurrentRange ,nil)

mp.add_forced_key_binding("d", moveWindowForwards ,nil , "repeatable")
mp.add_forced_key_binding("a", moveWindowBackwards,nil , "repeatable")

mp.add_forced_key_binding("w", superfastmoveWindowForwards ,nil , "repeatable")
mp.add_forced_key_binding("s", superfastmoveWindowBackwards,nil , "repeatable")

mp.add_forced_key_binding("W", superfastmoveWindowForwards ,nil , "repeatable")
mp.add_forced_key_binding("S", superfastmoveWindowBackwards,nil , "repeatable")

mp.add_forced_key_binding("D", fastmoveWindowForwards ,nil , "repeatable")
mp.add_forced_key_binding("A", fastmoveWindowBackwards,nil , "repeatable")

mp.add_key_binding("MOUSE_BTN3", incrementAR)
mp.add_key_binding("MOUSE_BTN4", decrementAR)

mp.add_key_binding("mouse_move", draw_cropper)
mp.observe_property("osd-width", "native", draw_cropper)
mp.observe_property("osd-height", "native", draw_cropper)

mp.add_key_binding("c", "easy_crop", easycrop_activate)
