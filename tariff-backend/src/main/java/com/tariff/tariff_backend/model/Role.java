package com.tariff.tariff_backend.model;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Entity
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Table(name="role", schema = "tariffs")
@Schema(description = "User role entity for access control")
public class Role {
    
    @Id
    @Schema(description = "Unique role identifier", example = "1")
    private Integer id;
    
    @Column(unique = true, nullable = false)
    @Schema(description = "Role name", example = "admin", required = true, allowableValues = {"admin", "user"})
    private String name;
}
