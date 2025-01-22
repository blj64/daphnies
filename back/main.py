from builtins import Exception, int, len, min, range, str
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import cv2
import numpy as np
from tempfile import NamedTemporaryFile
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware  
import subprocess
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Origine autorisée (URL de ton frontend)
    allow_credentials=True,
    allow_methods=["*"],  # Autoriser toutes les méthodes HTTP
    allow_headers=["*"],  # Autoriser tous les headers
)
# Répertoire temporaire pour stocker les vidéos
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


@app.post("/process-video/")
async def process_video(file: UploadFile = File(...)):
    # Vérifier si le fichier est une vidéo
    if not file.filename.endswith((".wmv", ".avi", ".mp4")):
        raise HTTPException(
            status_code=400, 
            detail="Le fichier doit être une vidéo (formats acceptés : .wmv, .avi, .mp4)"
        )
    
    # Extraire le nom de base et l'extension du fichier
    base_name, extension = os.path.splitext(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{base_name}_analyse_{timestamp}.mp4"
    
    # Sauvegarder la vidéo uploadée temporairement
    with NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        temp_file.write(await file.read())
        input_video_path = temp_file.name
    
    # Chemin de sortie intermédiaire pour la vidéo stabilisée
    stabilized_video_path = TEMP_DIR / f"{base_name}_stabilized_{timestamp}.avi"
    # Chemin de sortie final pour la vidéo convertie
    output_video_path = TEMP_DIR / output_filename

    try:
        # Ouvrir la vidéo
        cap = cv2.VideoCapture(input_video_path)

        # Obtenir les propriétés de la vidéo
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Définir un writer pour enregistrer la sortie
        out = cv2.VideoWriter(
            str(stabilized_video_path), 
            cv2.VideoWriter_fourcc(*'XVID'), 
            fps, 
            (frame_width, frame_height)
        )

        # Variables pour stabiliser les cercles
        previous_circles = None
        stabilization_factor = 0.5

        def detect_circles(frame):
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (9, 9), 2)
            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=100,
                param1=50,
                param2=30,
                minRadius=50,
                maxRadius=350
            )
            return circles

        # Parcourir les frames
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Détecter et stabiliser les cercles
            circles = detect_circles(frame)

            if circles is not None:
                circles = np.uint16(np.around(circles))
                if previous_circles is not None:
                    stabilized_circles = []
                    for i in range(min(len(circles[0]), len(previous_circles))):
                        x, y, r = circles[0][i]
                        x_prev, y_prev, r_prev = previous_circles[i]
                        x = int(stabilization_factor * x_prev + (1 - stabilization_factor) * x)
                        y = int(stabilization_factor * y_prev + (1 - stabilization_factor) * y)
                        r = int(stabilization_factor * r_prev + (1 - stabilization_factor) * r)
                        stabilized_circles.append([x, y, r])
                    stabilized_circles = np.array(stabilized_circles, dtype=np.uint16)
                else:
                    stabilized_circles = circles[0]

                mask = np.zeros_like(frame, dtype=np.uint8)
                for circle in stabilized_circles[:2]:
                    x, y, r = circle
                    r += 30
                    cv2.circle(mask, (x, y), r, (255, 255, 255), -1)
                    cv2.circle(frame, (x, y), r, (0, 255, 0), 2)

                extracted = cv2.bitwise_and(frame, mask)
                frame = extracted
                previous_circles = stabilized_circles

            # Enregistrer la frame
            out.write(frame)

        # Libérer les ressources
        cap.release()
        out.release()

        # Convertir la vidéo en MP4
        subprocess.run(
            ["ffmpeg", "-i", str(stabilized_video_path), "-vcodec", "libx264", "-acodec", "aac", str(output_video_path)],
            check=True
        )

        # Retourner la vidéo traitée
        return FileResponse(
            path=output_video_path,
            media_type="video/mp4",
            filename=output_filename
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement : {e}")
    finally:
        # Supprimer les fichiers temporaires
        os.remove(input_video_path)
        if stabilized_video_path.exists():
            os.remove(stabilized_video_path)
            
@app.get("/get-processed-video/")
async def get_processed_video():
    output_video_path = TEMP_DIR / "output_petri_dishes_stabilized.avi"

    # Vérifier si la vidéo traitée existe
    if not output_video_path.exists():
        raise HTTPException(status_code=404, detail="Aucune vidéo traitée trouvée.")

    # Retourner la vidéo traitée
    return FileResponse(
        path=output_video_path,
        media_type="video/x-msvideo",
        filename="output_petri_dishes_stabilized.avi"
    )
