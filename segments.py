def x_overlap_ratio(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b

    overlap = max(0, min(ax+aw, bx+bw)-max(ax, bx))
    narrower_width = min(aw, bw)

    return overlap/narrower_width if narrower_width else 0


def merge_rectangle(rect_a, rect_b):
    ax, ay, aw, ah = rect_a
    bx, by, bw, bh = rect_b

    x1, y1 = min(ax, bx), min(ay, by)
    x2, y2 = max(ax+aw, bx+bw), max(ay+ah, by+bh)

    return x1, y1, x2-x1, y2-y1


def belongs_to_segment(box, segment, y_gap_ratio, min_x_overlap_ratio):
    last_box = segment["boxes"][-1]
    x, y, w, h = box["rect"]
    last_x, last_y, last_w, last_h = last_box["rect"]

    vertical_gap = y - (last_y + last_h)
    allowed_gap = y_gap_ratio * max(h, last_h)

    return (vertical_gap<=allowed_gap and x_overlap_ratio(box["rect"], last_box["rect"])>=min_x_overlap_ratio)

def group_into_segments(boxes, y_gap_ratio, min_x_overlap_ratio):
    sorted_box = sorted(boxes, key=lambda b:(b["rect"][1], b["rect"][0]))

    segments = []
    for box in sorted_box:
        match = None
        for segment in segments:
            if belongs_to_segment(box, segment, y_gap_ratio, min_x_overlap_ratio):
                match = segment
                break
        if match:
            match["boxes"].append(box)
            match["rect"] = merge_rectangle(match["rect"], box["rect"])
        else:
            segments.append({"boxes":[box], "rect":box["rect"]})

    result = []
    for segment in segments:
        texts = []

        for box in segment["boxes"]:
            texts.append(box["text"])

        result.append({
            "rect" : segment["rect"],
            "text" : "\n".join(texts),
            "line_boxes" : segment["boxes"]
        })

    return result