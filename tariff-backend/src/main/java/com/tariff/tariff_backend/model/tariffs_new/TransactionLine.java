package com.tariff.tariff_backend.model.tariffs_new;

import java.time.Instant;
import java.util.Map;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import com.tariff.tariff_backend.model.User;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "transaction_line", schema = "tariffs")
@Schema(description = "Transaction record storing user tariff calculations")
public class TransactionLine {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "transactionid")
    @Schema(description = "Unique transaction identifier", example = "67890")
    private Integer transactionId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "userid", nullable = false)
    @Schema(description = "User who performed the calculation", required = true)
    private User user;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    @Schema(description =  "Time Tariff was created")
    private Instant created_at;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "snapshot", columnDefinition = "jsonb")
    @Schema(description = "Snapshot of the tariff calculation at the time of transaction")
    private Map<String,Object> snapshot;
}
