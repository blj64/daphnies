<template>
  <div>
    <h1>Daphnies Watcher</h1>
    
    <input type="file" @change="handleFileUpload" accept="video/wmv" />
    <button v-if="selectedFile && !isLoading" @click="sendVideo">Convertir</button>
    
    <div v-if="isLoading" class="loader"></div>

    <div v-if="videoUrl && !isLoading">
      <h2>Vidéo analysé :</h2>
      <video controls :src="videoUrl" type="video/mp4"></video>
      <a :href="videoUrl" download="video.mp4">Télécharger la vidéo</a>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      selectedFile: null,
      videoUrl: null,
      isLoading: false,
    };
  },
  methods: {
    handleFileUpload(event) {
      this.selectedFile = event.target.files[0];
    },
    async sendVideo() {
      if (!this.selectedFile) {
        alert("Veuillez sélectionner une vidéo !");
        return;
      }

      const formData = new FormData();
      formData.append("file", this.selectedFile);

      this.isLoading = true;

      try {
        const response = await axios.post(
          "http://localhost:8000/process-video/",
          formData,
          { responseType: "blob" } // Recevoir la vidéo convertie en tant que blob
        );

        const blob = new Blob([response.data], { type: "video/mp4" });
        this.videoUrl = URL.createObjectURL(blob);
      } catch (error) {
        console.error("Erreur lors de l'envoi de la vidéo :", error);
        alert("Une erreur est survenue lors du traitement de la vidéo.");
      } finally {
        this.isLoading = false;
      }
    },
  },
};
</script>

<style>
.loader {
  margin: 20px auto;
  border: 5px solid #f3f3f3; /* Gris clair */
  border-top: 5px solid #3498db; /* Bleu */
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
