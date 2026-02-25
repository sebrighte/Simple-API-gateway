class cls_services {
    constructor(json_services) {
        this.services = json_services.map(
            ({ name, endpoint, swagger }) => new cls_service(name, endpoint, swagger)
        );
    }
    getService(name) {
        return this.services.find((service) => service.name === name) || null;
    }

    addService(name, endpoint, swagger) {
        this.services.push(new cls_service(name, endpoint, swagger));
        this.syncService();
        return new cls_services(JSON.parse(JSON.stringify(this.services)));
    }

    removeService(name) {
        this.services = this.services.filter((service) => service.name !== name);
        this.syncService();
        return new cls_services(JSON.parse(JSON.stringify(this.services)));
    }

    updateService(title, base, swagger) {
        const service = this.getService(title);
        service.title = title;
        service.endpoint = base;
        service.swagger = swagger;
        return new cls_services(JSON.parse(JSON.stringify(this.services)));
    }

    async syncService() {
        let endpoint = "/update";
        try {
            const response = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(this),
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(`HTTP ${response.status}: ${text}`);
            }

            return await response.json();
        } catch (err) {
            console.error("POST failed:", err);
            throw err;
        }
    }
}

class cls_service {
    constructor(name, endpoint, swagger) {
        this.name = name;
        this.endpoint = endpoint;
        this.swagger = swagger;
    }
}

const { useState, useEffect, exports } = React;
const { createRoot } = ReactDOM;
const { useRef } = React;

const Sidebar = ({ setMenu, setTitle }) => {
    const [specs, setSpecs] = useState([]);//useState(["traccar", "homeassistant"]);
    function handleClick(action, title) {
        setMenu(action);
    }

    useEffect(() => {
        fetch("/files")   // ← your endpoint
            .then(res => res.json())
            .then(data => setSpecs(data))
            .catch(err => console.error("Error loading files:", err));
    }, []);

    return (
        <div className="sidebar">
            <img
                src="/static/logo.png"
                alt="Sebright Software Logo"
                width="100%"
            />
            <a>
                <h1>API Gateway</h1>
            </a>
            <h2>Main Menu</h2>
            <ul>
                <li onClick={() => handleClick("Home", "API Overview")}>Overview</li>
                <li onClick={() => handleClick("APIs", "Add or Edit APIs")}>
                    Manage APIs
                </li>
                <li onClick={() => window.open("/docs", "_blank")}>Gateway OpenAPI</li>
            </ul>

            <h2>Local OpenAPI</h2>
            <ul>
                {specs.map(name => (
                   <li key={name}><a target="_blank" rel="noreferrer" href={`/swaggerfile/${name}`}>{name}</a></li>
                ))}
            </ul>
        </div>
    );
};

const Topbar = ({ title }) => (
    <div className="topbar">
        <strong>{title}</strong>
    </div>
);

const Panel = ({ services, menu }) => {
    if (!services || services.length === 0) return null;
    if (menu == "Home") {
        return (
            <div className="main">
                <br />
                <strong>List of Current Services in this Gateway</strong>
                <ul>
                    {services.services.map((service) => (
                        <li key={service.name}>
                            <i>
                                {service.name} ({service.endpoint})
                            </i>
                        </li>
                    ))}
                </ul>
            </div>
        );
    }
};

function ServiceEditor({ services, menu, setServices }) {
    const [editing, setEditing] = useState(null);
    const [form, setForm] = useState({ name: "", endpoint: "", swagger: "" });
    const [status, setStatus] = useState("");

    if (!services || services.length === 0) return null;
    const startEdit = (title) => {
        setEditing(title);
        setStatus("");
        setForm({
            title,
            base: services.getService(title).endpoint,
            swagger: services.getService(title).swagger,
        });
    };

    const startCreate = () => {
        setEditing("new");
        setForm({
            title: "newtides",
            base: "https://sebright.uksouth.cloudapp.azure.com/api/TidesSDK/k",
            swagger: "swagger/docs/v1",
        });
    };

    const add = () => {
        if (!form.title || !form.base || !form.swagger) {
            alert("All fields are required");
            return;
        }
        setServices(services.addService(form.title, form.base, form.swagger));
        setEditing(null);
    };

    const remove = (title) => {
        if (confirm("Are you sure you want to continue?")) {
            setServices(services.removeService(title));
            setEditing(null);
        } else {
            console.log("Cancelled.");
        }
    };

    const update = (title) => {
        if (!form.title || !form.base) {
            alert("All fields are required");
            return;
        }
        setServices(services.updateService(form.title, form.base, form.swagger));
        setEditing(null);
    };

    const checkStatus = (url) => {
        fetch(`/check-website?url=${url}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.exists) {
                    setStatus("✅");
                } else {
                    setStatus("❌");
                }
            });
    };

    const openSwagger = (serviceName) => {
        if (!serviceName) return;
        const url = `/swagger/${serviceName}`;
        window.open(url, "_blank"); // Opens in a new tab
    };

    const openOrigSwagger = (title, base, swagger) => {
        const url = `/origswagger/${title}/${base}${swagger}`;
        window.open(url, "_blank"); // Opens in a new tab
    };

    if (menu == "APIs") {
        return (
            <div className="service-editor">
                <h2>Service Registry</h2>

                <ul className="service-list">
                    {services.services.map((service) => (
                        <li key={service.name} className="service-item">
                            <strong>{service.name}</strong>
                            <div className="service-details">
                                <small>{"Base URL: " + service.endpoint}</small>
                                <small>{"OpenAPI: " + service.swagger}</small>
                                <small>
                                    <a
                                        href={service.swagger}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        Link
                                    </a>
                                </small>
                            </div>
                            <div className="service-actions">
                                <button
                                    className="button-4"
                                    onClick={() => startEdit(service.name)}
                                >
                                    Edit
                                </button>
                                <button
                                    className="button-4"
                                    onClick={() => remove(service.name)}
                                >
                                    Delete
                                </button>
                                <button
                                    className="button-4"
                                    onClick={() => openSwagger(service.name)}
                                >
                                    Test
                                </button>
                            </div>
                        </li>
                    ))}
                </ul>

                <button className="button-4" onClick={startCreate}>
                    Add New Service
                </button>

                {editing && (
                    <div className="editor-panel">
                        <h3>
                            {editing === "new"
                                ? "Create Service"
                                : "Edit '" + form.title + "' Service"}
                        </h3>

                        <label>
                            Name:
                            <input
                                readOnly={editing !== "new"}
                                value={form.title}
                                onChange={(e) => setForm({ ...form, title: e.target.value })}
                            />
                        </label>

                        <label>
                            Base URL:
                            <input
                                value={form.base}
                                onChange={(e) => setForm({ ...form, base: e.target.value })}
                            />
                        </label>

                        <label>
                            Swagger Path:
                            <input
                                value={form.swagger}
                                onChange={(e) => setForm({ ...form, swagger: e.target.value })}
                            />
                        </label>

                        <div className="editor-actions">
                            {editing === "new" ? (
                                <button className="button-4" onClick={add}>
                                    Save
                                </button>
                            ) : (
                                <button className="button-4" onClick={update}>
                                    Update
                                </button>
                            )}
                            <button className="button-4" onClick={() => setEditing(null)}>
                                Cancel
                            </button>
                            <button
                                className="button-4"
                                onClick={() =>
                                    openOrigSwagger(form.title, form.base, form.swagger)
                                }
                            >
                                Get Swagger
                            </button>
                            <button
                                className="button-4"
                                onClick={() => checkStatus(form.base, form.swagger)}
                            >
                                Check Endpoint{status}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        );
    }
}

const SwaggerComponent = ({ menu, swagger, services }) => {
    const swaggerRef = React.useRef(null);
    const swaggerInstanceRef = React.useRef(null);

    useEffect(() => {
        if (menu.includes("Swagger") && swaggerRef.current) {
            swaggerInstanceRef.current = SwaggerUIBundle({
                url: "openapi.json",
                domNode: swaggerRef.current,
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
                layout: "BaseLayout",
            });
        }
        return () => {
            if (swaggerRef.current) {
                swaggerRef.current.innerHTML = "";
            }
            swaggerInstanceRef.current = null;
        };
    }, [menu]);

    return <div ref={swaggerRef} />;
};

function fetchJSON(url, passedFunction = null) {
    fetch(url)
        .then((res) => {
            if (!res.ok) {
                throw new Error("Failed to fetch");
            }
            return res.json();
        })
        .then((data) => {
            passedFunction(data);
            return data;
        });
}

const App = () => {
    const [services, setServices] = useState([]);
    const [swagger, setSwagger] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [menu, setMenu] = useState("APIs");
    const [title, setTitle] = useState("Gateway Settings");

    useEffect(() => {
        fetch("/services")
            .then((res) => res.json())
            .then((json_services) => {
                setServices(new cls_services(json_services));
            })
            .catch((err) => console.error("Failed loading services:", err));
    }, []); // 👈 runs once when component mounts

    return (
        <div className="app">
            <Sidebar setMenu={setMenu} />
            <div className="main">
                <Topbar title={title} />
                <Panel services={services} menu={menu} />
                <ServiceEditor
                    menu={menu}
                    services={services}
                    setServices={setServices}
                />
            </div>
        </div>
    );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
