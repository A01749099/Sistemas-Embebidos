def process_frame(frame, model_test, image_cropper, service):
    prediction = np.zeros((1, 3))
    image_bbox = model_test.get_bbox(frame)

    if image_bbox is None:
        return frame, "No Face Detected"

    for model_name in os.listdir(MODEL_DIR):
        h_input, w_input, model_type, scale = parse_model_name(model_name)
        param = {
            "org_img": frame,
            "bbox": image_bbox,
            "scale": scale,
            "out_w": w_input,
            "out_h": h_input,
            "crop": True,
        }
        if scale is None:
            param["crop"] = False
        img = image_cropper.crop(**param)
        prediction += model_test.predict(img, os.path.join(MODEL_DIR, model_name))

    label = np.argmax(prediction)
    value = prediction[0][label] / 2
    color = (0, 255, 0) if label == 1 else (0, 0, 255)
    result_text = f"{'Real Face' if label == 1 else 'Fake Face'}: {value:.2f}"

    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Desconocido"
        is_photo = "foto" if label == 1 else "persona"
        
        if True in matches:
            name = known_face_names[matches.index(True)]
        
        info_text = f"{name} y {is_photo}"
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, info_text, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

        if name == "Desconocido":
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            unknown_image_path = f"unknown_{timestamp}.jpg"
            cv2.imwrite(unknown_image_path, frame)
            upload_to_drive(service, unknown_image_path, UNKNOWN_FOLDER_ID)
            os.remove(unknown_image_path)

    return frame, result_text
