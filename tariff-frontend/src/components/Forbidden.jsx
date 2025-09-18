export function Forbidden() {
    return (
        <div className="fixed inset-0 z-50 bg-white">
            <span
                className="absolute top-0 left-0 m-0 p-0 text-2xl font-bold text-black"
                style={{ fontFamily: "Times New Roman, Times, serif" }}
            >
                Forbidden
            </span>
        </div>
    );
}