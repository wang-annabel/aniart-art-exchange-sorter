import { useRef } from "react";

function UploadBtn({ apiBase, token, onUpdateMatchingCache }) {
  const fileInputRef = useRef(null);

  // Trigger the hidden file input when button is clicked
  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      console.log("uploading file", file.name);
      console.log("Token available:", !!token);
      console.log(
        "Token value:",
        token ? token.substring(0, 20) + "..." : "null"
      );

      // 1. upload file
      const formData = new FormData();
      formData.append("file", file);

      // Build headers - include auth token if available
      const headers = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
        console.log("Adding Authorization header");
      } else {
        console.log("No token, skipping Authorization header");
      }

      console.log("Request headers:", headers);

      const fileResponse = await fetch(`${apiBase}/files/upload`, {
        method: "POST",
        headers: headers,
        body: formData,
      });

      if (!fileResponse.ok) {
        const errorData = await fileResponse.json();
        throw new Error(errorData.detail || "File upload failed.");
      }

      const fileData = await fileResponse.json();
      const fileId = fileData.file_id;

      // 2. create matching
      const matchResponse = await fetch(
        `${apiBase}/matchings?file_id=${fileId}`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );

      if (!matchResponse.ok) {
        const errorData = await matchResponse.json();
        throw new Error(errorData.detail || "Matching creation failed");
      }

      const matchData = await matchResponse.json();
      const matchingId = matchData.matching_id;
      console.log("Matching created, ID:", matchingId);

      // 3. update matching cache
      onUpdateMatchingCache(matchingId, fileId);
      // reset file input
      event.target.value = "";
    } catch (error) {
      console.error("Upload error:", error);
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
      <button className="upload-btn" onClick={handleButtonClick}>
        <span>
          <img id="upload-btn-icon" src="/upload.png" alt="Upload icon" />
        </span>
        <span>Upload CSV</span>
      </button>
    </>
  );
}

export default UploadBtn;
