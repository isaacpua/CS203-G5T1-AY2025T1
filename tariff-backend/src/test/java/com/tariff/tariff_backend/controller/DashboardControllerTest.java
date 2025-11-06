package com.tariff.tariff_backend.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tariff.tariff_backend.config.ApplicationConfig;
import com.tariff.tariff_backend.config.CorsConfig;
import com.tariff.tariff_backend.config.SecurityConfiguration;
import com.tariff.tariff_backend.dto.TariffPatchDTO;
import com.tariff.tariff_backend.model.dashboard.DashboardMetrics;
import com.tariff.tariff_backend.model.dashboard.DashboardResponse;
import com.tariff.tariff_backend.security.JwtAuthenticationEntryPoint;
import com.tariff.tariff_backend.security.JwtAuthenticationFilter;
import com.tariff.tariff_backend.service.DashboardService;
import com.tariff.tariff_backend.service.JwtService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.data.domain.Pageable;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Collections;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(DashboardController.class)
// FIX: Import CorsConfig to provide the CorsFilter bean
@Import({
    SecurityConfiguration.class, 
    CorsConfig.class,
    JwtAuthenticationEntryPoint.class, 
    JwtAuthenticationFilter.class   
})public class DashboardControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private DashboardService dashboardService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private ApplicationConfig applicationConfig;



    // --- Tests for GET /tariffs (Public Endpoint) ---

    @Test
    @WithMockUser
    public void getTariffs_WhenPaginated_ShouldReturnMetrics() throws Exception {
        DashboardMetrics mockMetrics = new DashboardMetrics(Collections.emptyList(), 0, 0, 0);
        when(dashboardService.getTariffs(
                any(), any(), any(Pageable.class), any(), any()
        )).thenReturn(mockMetrics);

        mockMvc.perform(get("/api/v1/dashboard/tariffs")
                        .param("page", "0")
                        .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content").isArray());
    }


    @Test
    @WithMockUser(roles = "ADMIN")
    public void createTariff_AsAdmin_ShouldSucceed() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        TariffPatchDTO requestBody = new TariffPatchDTO();
        DashboardResponse successResponse = new DashboardResponse(true, "Tariff created");

        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(true);
        when(dashboardService.createTariff(any(TariffPatchDTO.class))).thenReturn(successResponse);

        mockMvc.perform(post("/api/v1/dashboard/tariffs")
                        .header("Authorization", authHeader)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestBody)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.message").value("Tariff created"));
    }

    @Test
    public void createTariff_Unauthenticated_ShouldBeForbidden() throws Exception {
        TariffPatchDTO requestBody = new TariffPatchDTO();

        mockMvc.perform(post("/api/v1/dashboard/tariffs")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestBody)))
                .andExpect(status().isUnauthorized()) // This is 401
                .andExpect(jsonPath("$.message").value("Access denied: Full authentication is required to access this resource"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void createTariff_AsAdmin_WhenServiceFails_ShouldReturnBadRequest() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        TariffPatchDTO requestBody = new TariffPatchDTO();
        DashboardResponse failResponse = new DashboardResponse(false, "Failed to create");

        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(true);
        when(dashboardService.createTariff(any(TariffPatchDTO.class))).thenReturn(failResponse);

        mockMvc.perform(post("/api/v1/dashboard/tariffs")
                        .header("Authorization", authHeader)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestBody)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.success").value(false))
                .andExpect(jsonPath("$.message").value("Failed to create"));
    }
    
    @Test
    @WithMockUser(roles = "ADMIN")
    public void createTariff_AsAdmin_ShouldFail_WhenServiceFails() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        TariffPatchDTO requestBody = new TariffPatchDTO();
        DashboardResponse failResponse = new DashboardResponse(false, "Failed");

        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(true);
        when(dashboardService.createTariff(any(TariffPatchDTO.class))).thenReturn(failResponse);

        mockMvc.perform(post("/api/v1/dashboard/tariffs")
                        .header("Authorization", authHeader)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestBody)))
                .andExpect(status().isBadRequest()) // 400
                .andExpect(jsonPath("$.success").value(false));
    }

    @Test
    @WithMockUser(roles = "USER")
    public void createTariff_AsUser_ShouldBeForbidden() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        TariffPatchDTO requestBody = new TariffPatchDTO();

        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(false);

        mockMvc.perform(post("/api/v1/dashboard/tariffs")
                        .header("Authorization", authHeader)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestBody)))
                .andExpect(status().isForbidden()); // 403
    }

    // Test for the "size <= 0" branch in getTariffs
    @Test
    @WithMockUser
    public void getTariffs_WhenSizeIsZero_ShouldReturnAllTariffs() throws Exception {
        when(dashboardService.getAllTariffs()).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/v1/dashboard/tariffs")
                        .param("size", "0")) // Test size=0
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tariffs").isArray());
        
        mockMvc.perform(get("/api/v1/dashboard/tariffs")
                        .param("size", "-1")) // Test size < 0
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tariffs").isArray());
    }

    // --- Tests for PATCH /tariffs/{tariffid} ---

    @Test
    @WithMockUser(roles = "ADMIN")
    public void updateTariff_AsAdmin_ShouldSucceed() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        TariffPatchDTO requestBody = new TariffPatchDTO();
        DashboardResponse successResponse = new DashboardResponse(true, "Tariff updated");

        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(true);
        when(dashboardService.updateTariff(eq("t1"), any(TariffPatchDTO.class))).thenReturn(successResponse);

        mockMvc.perform(patch("/api/v1/dashboard/tariffs/{tariffid}", "t1")
                        .header("Authorization", authHeader)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestBody)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void updateTariff_AsAdmin_WhenServiceFails_ShouldReturnBadRequest() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        TariffPatchDTO requestBody = new TariffPatchDTO();
        DashboardResponse failResponse = new DashboardResponse(false, "Not found");

        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(true);
        when(dashboardService.updateTariff(eq("t1"), any(TariffPatchDTO.class))).thenReturn(failResponse);

        mockMvc.perform(patch("/api/v1/dashboard/tariffs/{tariffid}", "t1")
                        .header("Authorization", authHeader)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestBody)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.success").value(false));
    }

    @Test
    @WithMockUser(roles = "USER")
    public void updateTariff_AsUser_ShouldBeForbidden() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(false);

        mockMvc.perform(patch("/api/v1/dashboard/tariffs/{tariffid}", "t1")
                        .header("Authorization", authHeader)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(new TariffPatchDTO())))
                .andExpect(status().isForbidden());
    }

    // --- Tests for DELETE /tariffs/{tariffid} ---

    @Test
    @WithMockUser(roles = "ADMIN")
    public void deleteTariff_AsAdmin_ShouldSucceed() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        DashboardResponse successResponse = new DashboardResponse(true, "Tariff deleted");

        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(true);
        when(dashboardService.deleteTariff("t1")).thenReturn(successResponse);

        mockMvc.perform(delete("/api/v1/dashboard/tariffs/{tariffid}", "t1")
                        .header("Authorization", authHeader))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    public void deleteTariff_AsAdmin_WhenServiceFails_ShouldReturnBadRequest() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        DashboardResponse failResponse = new DashboardResponse(false, "Not found");

        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(true);
        when(dashboardService.deleteTariff("t1")).thenReturn(failResponse);

        mockMvc.perform(delete("/api/v1/dashboard/tariffs/{tariffid}", "t1")
                        .header("Authorization", authHeader))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.success").value(false));
    }

    @Test
    @WithMockUser(roles = "USER")
    public void deleteTariff_AsUser_ShouldBeForbidden() throws Exception {
        String token = "dummy-token";
        String authHeader = "Bearer " + token;
        when(jwtService.getTokenFromHeader(authHeader)).thenReturn(token);
        when(jwtService.hasRole(token, "admin")).thenReturn(false);

        mockMvc.perform(delete("/api/v1/dashboard/tariffs/{tariffid}", "t1")
                        .header("Authorization", authHeader))
                .andExpect(status().isForbidden());
    }
}